
from contextlib import asynccontextmanager
from datetime import date as date_type
from io import BytesIO
from pathlib import Path
import math
import uuid
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from PIL import Image, UnidentifiedImageError

from database import (
    init_db,
    save_dog_report,
    get_reports,
    save_match,
    get_matches,
)

from dog_detector import crop_dog
from dino_embeddings import embed

from vector_search import (
    rebuild_indexes,
    add_dog_embedding,
    search_opposite_category,
)


# --------------------------------------------------
# Project paths and configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORT_IMAGES_DIR = PROJECT_ROOT / "data" / "report_images"

REPORT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


SRI_LANKAN_DISTRICTS = {
    "Ampara",
    "Anuradhapura",
    "Badulla",
    "Batticaloa",
    "Colombo",
    "Galle",
    "Gampaha",
    "Hambantota",
    "Jaffna",
    "Kalutara",
    "Kandy",
    "Kegalle",
    "Kilinochchi",
    "Kurunegala",
    "Mannar",
    "Matale",
    "Matara",
    "Monaragala",
    "Mullaitivu",
    "Nuwara Eliya",
    "Polonnaruwa",
    "Puttalam",
    "Ratnapura",
    "Trincomalee",
    "Vavuniya",
}


# --------------------------------------------------
# Application startup and shutdown
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    # Rebuild both FAISS indexes from SQLite.
    rebuild_indexes()

    print("Pawprint application started successfully.")

    yield

    print("Pawprint application shutting down.")


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Pawprint API",
    description="Lost Dog Matcher using YOLOv8, DINOv2 and FAISS",
    version="2.1.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# Serve uploaded dog photographs
# --------------------------------------------------

app.mount(
    "/report-images",
    StaticFiles(directory=str(REPORT_IMAGES_DIR)),
    name="report-images",
)


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def clean_value(value):
    """Convert values into JSON-safe values."""

    if isinstance(value, dict):
        return {
            str(key): clean_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            clean_value(item)
            for item in value
        ]

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, bytes):
        return None

    if value is None or isinstance(
        value,
        (str, int, float, bool)
    ):
        return value

    return str(value)


def validate_image(image_bytes):
    """Open and validate an uploaded image."""

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    try:
        return Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image.",
        )


def public_report_fields(report):
    """Return public report information without embeddings or contact details."""

    return {
        key: clean_value(value)
        for key, value in report.items()
        if key not in {"embedding", "contact"}
    }


def validate_status(status):
    """Validate lost/found status."""

    status = status.strip().lower()

    if status not in {"lost", "found"}:
        raise HTTPException(
            status_code=400,
            detail="Status must be either lost or found.",
        )

    return status


def validate_district(district):
    """Validate a Sri Lankan district."""

    district = district.strip().title()

    if district not in SRI_LANKAN_DISTRICTS:
        raise HTTPException(
            status_code=400,
            detail="Please select a valid Sri Lankan district.",
        )

    return district


def generate_embedding(image):
    """Generate and validate a DINOv2 embedding from a dog image."""

    cropped_image = crop_dog(image)

    embedding = np.asarray(
        embed(cropped_image),
        dtype=np.float32,
    ).reshape(-1)

    if embedding.shape != (768,):
        raise ValueError(
            "DINOv2 embedding must contain 768 values."
        )

    if not np.isfinite(embedding).all():
        raise ValueError(
            "The generated embedding contains invalid values."
        )

    return embedding


# --------------------------------------------------
# Home endpoint
# --------------------------------------------------

@app.get("/")
async def home():

    return {
        "message": "Welcome to Pawprint!",
        "status": "running",
    }


# --------------------------------------------------
# Health check endpoint
# --------------------------------------------------

@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "application": "Pawprint",
    }


# --------------------------------------------------
# Submit a lost/found dog report
# --------------------------------------------------

@app.post("/report")
async def create_report(
    file: UploadFile = File(...),
    status: str = Form(...),
    district: str = Form(...),
    date: str = Form(...),
    reporter_name: str = Form(...),
    contact: str = Form(...),
    dog_name: str = Form(None),
    size: str = Form(None),
    color: str = Form(None),
):

    image_path = None
    report_saved = False

    try:

        # 1. Validate status.
        status = validate_status(status)

        # 2. Validate district.
        district = validate_district(district)

        # 3. Validate reporter information.
        reporter_name = reporter_name.strip()
        contact = contact.strip()

        if not reporter_name:
            raise HTTPException(
                status_code=400,
                detail="Reporter name is required.",
            )

        if not contact:
            raise HTTPException(
                status_code=400,
                detail="Contact information is required.",
            )

        # 4. Validate date.
        try:
            report_date = date_type.fromisoformat(date)

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Date must use YYYY-MM-DD format.",
            )

        # 5. Validate optional size.
        if size:
            size = size.strip().lower()

            if size not in {"small", "medium", "large"}:
                raise HTTPException(
                    status_code=400,
                    detail="Size must be small, medium or large.",
                )
        else:
            size = None

        # 6. Read and validate uploaded image.
        image_bytes = await file.read()
        image = validate_image(image_bytes)

        # 7. Generate DINOv2 embedding using YOLOv8 crop.
        report_embedding = generate_embedding(image)

        # 8. Save original photograph.
        image_filename = f"{uuid.uuid4().hex}.jpg"

        image_path = REPORT_IMAGES_DIR / image_filename

        image.save(
            image_path,
            format="JPEG",
            quality=90,
        )

        relative_image_path = str(
            image_path.relative_to(PROJECT_ROOT)
        )

        cleaned_dog_name = (
            dog_name.strip()
            if dog_name and dog_name.strip()
            else None
        )

        cleaned_color = (
            color.strip()
            if color and color.strip()
            else None
        )

        # 9. Save report in SQLite.
        report_id = save_dog_report(
            dog_name=cleaned_dog_name,
            status=status,
            image_path=relative_image_path,
            district=district,
            date=report_date.isoformat(),
            size=size,
            color=cleaned_color,
            reporter_name=reporter_name,
            contact=contact,
            embedding=report_embedding,
        )

        report_saved = True

        # 10. Add embedding to the correct FAISS index.
        report_metadata = {
            "dog_name": cleaned_dog_name,
            "image_path": relative_image_path,
            "district": district,
            "date": report_date.isoformat(),
            "size": size,
            "color": cleaned_color,
        }

        add_dog_embedding(
            status=status,
            report_id=report_id,
            embedding=report_embedding,
            metadata=report_metadata,
        )

        # 11. Search the opposite category.
        candidates = search_opposite_category(
            query_embedding=report_embedding,
            new_status=status,
            k=10,
            district=district,
            date=report_date.isoformat(),
            size=size,
        )

        potential_matches = []

        for candidate in candidates:

            candidate_id = candidate.get("id")

            if candidate_id is None:
                continue

            # Store IDs in the correct lost/found order.
            if status == "lost":
                lost_dog_id = report_id
                found_dog_id = candidate_id

            else:
                lost_dog_id = candidate_id
                found_dog_id = report_id

            # Save potential match.
            save_match(
                lost_dog_id=lost_dog_id,
                found_dog_id=found_dog_id,
                similarity=float(candidate["similarity"]),
            )

            potential_matches.append({
                "report_id": clean_value(candidate_id),
                "dog_name": clean_value(candidate.get("dog_name")),
                "image_path": clean_value(candidate.get("image_path")),
                "district": clean_value(candidate.get("district")),
                "date": clean_value(candidate.get("date")),
                "size": clean_value(candidate.get("size")),
                "color": clean_value(candidate.get("color")),
                "similarity": round(
                    float(candidate["similarity"]),
                    4,
                ),
                "same_district": bool(
                    candidate.get("same_district", False)
                ),
            })

        return {
            "status": "success",
            "message": "Dog report submitted successfully.",
            "report_id": report_id,
            "dog_name": cleaned_dog_name,
            "report_status": status,
            "district": district,
            "image_path": relative_image_path,
            "embedding_dimension": int(report_embedding.size),
            "total_potential_matches": len(potential_matches),
            "potential_matches": potential_matches,
        }

    except HTTPException:

        if image_path is not None and not report_saved:
            if image_path.exists():
                image_path.unlink()

        raise

    except ValueError as error:

        if image_path is not None and not report_saved:
            if image_path.exists():
                image_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        if image_path is not None and not report_saved:
            if image_path.exists():
                image_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        await file.close()


# --------------------------------------------------
# AI Search for potential lost/found dog matches
# --------------------------------------------------

@app.post("/search")
async def search_dog(
    file: UploadFile = File(...),
    status: str = Form(...),
    district: str = Form(...),
    date: str = Form(...),
    size: str = Form(None),
    color: str = Form(None),
    dog_name: str = Form(None),
    k: int = Form(10),
):
    """
    Search existing reports for visually similar dogs.

    This endpoint does not create a new report.

    Lost searches Found.
    Found searches Lost.
    """

    try:

        # 1. Validate status.
        status = validate_status(status)

        # 2. Validate district.
        district = validate_district(district)

        # 3. Validate date.
        try:
            search_date = date_type.fromisoformat(date)

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Date must use YYYY-MM-DD format.",
            )

        # 4. Validate optional size.
        if size:
            size = size.strip().lower()

            if size not in {"small", "medium", "large"}:
                raise HTTPException(
                    status_code=400,
                    detail="Size must be small, medium or large.",
                )
        else:
            size = None

        # 5. Validate number of results.
        if k < 1 or k > 50:
            raise HTTPException(
                status_code=400,
                detail="Number of matches must be between 1 and 50.",
            )

        # 6. Read and validate required photograph.
        image_bytes = await file.read()
        image = validate_image(image_bytes)

        # 7. Generate DINOv2 embedding using YOLOv8 crop.
        query_embedding = generate_embedding(image)

        # 8. Search opposite category using FAISS.
        candidates = search_opposite_category(
            query_embedding=query_embedding,
            new_status=status,
            k=k,
            district=district,
            date=search_date.isoformat(),
            size=size,
        )

        # 9. Prepare potential matches.
        potential_matches = []

        for rank, candidate in enumerate(candidates, start=1):

            similarity = float(candidate["similarity"])

            potential_matches.append({
                "rank": rank,
                "report_id": clean_value(candidate.get("id")),
                "dog_name": clean_value(candidate.get("dog_name")),
                "status": clean_value(candidate.get("status")),
                "image_path": clean_value(candidate.get("image_path")),
                "district": clean_value(candidate.get("district")),
                "date": clean_value(candidate.get("date")),
                "size": clean_value(candidate.get("size")),
                "color": clean_value(candidate.get("color")),
                "similarity": round(similarity, 4),
                "similarity_percentage": round(
                    similarity * 100,
                    2,
                ),
                "same_district": bool(
                    candidate.get("same_district", False)
                ),
            })

        return {
            "status": "success",
            "message": "AI dog search completed successfully.",

            "search_details": {
                "dog_name": (
                    dog_name.strip()
                    if dog_name and dog_name.strip()
                    else None
                ),
                "search_status": status,
                "target_status": (
                    "found" if status == "lost" else "lost"
                ),
                "district": district,
                "date": search_date.isoformat(),
                "size": size,
                "color": (
                    color.strip()
                    if color and color.strip()
                    else None
                ),
            },

            "total_matches": len(potential_matches),
            "matches": potential_matches,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        await file.close()


# --------------------------------------------------
# Retrieve lost/found reports
# --------------------------------------------------

@app.get("/reports")
async def list_reports(
    status: str = Query(None),
):

    if status is not None:
        status = validate_status(status)

    reports = get_reports(status)

    return {
        "status": "success",
        "total_reports": len(reports),
        "reports": [
            public_report_fields(report)
            for report in reports
        ],
    }




# --------------------------------------------------
# District report summary for the map
# --------------------------------------------------

@app.get("/district-summary")
async def get_district_summary():
    """
    Return lost/found report counts for each Sri Lankan district.
    This endpoint returns aggregate counts only, not report details.
    """

    district_counts = {
        district: {
            "district": district,
            "lost": 0,
            "found": 0,
            "total": 0,
        }
        for district in SRI_LANKAN_DISTRICTS
    }

    lost_reports = get_reports("lost")
    found_reports = get_reports("found")

    for report in lost_reports:
        district = report.get("district")

        if district in district_counts:
            district_counts[district]["lost"] += 1
            district_counts[district]["total"] += 1

    for report in found_reports:
        district = report.get("district")

        if district in district_counts:
            district_counts[district]["found"] += 1
            district_counts[district]["total"] += 1

    return {
        "status": "success",
        "total_lost": len(lost_reports),
        "total_found": len(found_reports),
        "total_reports": len(lost_reports) + len(found_reports),
        "districts": sorted(
            district_counts.values(),
            key=lambda item: item["district"],
        ),
    }



# --------------------------------------------------
# Retrieve potential matches for a report
# --------------------------------------------------

@app.get("/matches/{status}/{report_id}")
async def list_report_matches(
    status: str,
    report_id: int,
):

    status = validate_status(status)

    if status == "lost":

        matches = get_matches(
            lost_dog_id=report_id
        )

    else:

        matches = get_matches(
            found_dog_id=report_id
        )

    return {
        "status": "success",
        "report_id": report_id,
        "report_status": status,
        "total_matches": len(matches),
        "matches": [
            clean_value(match)
            for match in matches
        ],
    }
