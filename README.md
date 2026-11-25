Pawprint

Lost Dog Matcher

Pawprint is an AI-powered lost dog matching application designed to help reunite lost dogs with their owners. Users can report lost or found dogs by uploading photographs and providing relevant information. The system analyzes dog images and searches for visually similar reports to identify potential matches.

Unlike traditional systems that rely only on manual descriptions, Pawprint uses computer vision and image embeddings to compare dog photographs and rank possible matches.

Features

Lost Dog Reporting – Submit lost dog reports with photographs and relevant details.

Found Dog Reporting – Upload information about dogs that have been found.

AI-Based Dog Detection – Detect and crop dogs from uploaded images using YOLO.

Visual Similarity Matching – Generate image embeddings using DINOv2 to compare dog appearances.

Vector Similarity Search – Use FAISS to retrieve visually similar dog images.

Metadata-Based Filtering – Refine potential matches using information such as location, date, and dog size.

Ranked Matching Results – Display potential matches based on visual similarity and available metadata.

Interactive Map – Explore lost and found dog reports by district in Sri Lanka.

District-Based Report View – Select a district to view reports associated with that area.

How It Works

Pawprint follows an AI-based image matching pipeline:

Image Upload – A user uploads a photograph of a lost or found dog.

Dog Detection and Cropping – YOLO detects the dog and extracts the relevant image region.

Feature Extraction – DINOv2 generates a numerical embedding representing the visual features of the dog.

Vector Search – FAISS searches for visually similar embeddings in the database.

Metadata Filtering – Candidate matches are refined using available report information, including location, date, and size.

Match Ranking – Potential matches are ranked and presented to the user.

Technology Stack

Component

Technology

Frontend

React, TypeScript, Vite

Backend

Python, FastAPI

Dog Detection

YOLO

Image Embeddings

DINOv2

Vector Search

FAISS

Database

SQLite

Image Processing

Pillow

Map Visualization

GeoJSON


Data and Models

The application uses SQLite to store report information and local files to store uploaded images.

The AI matching pipeline uses:

YOLO for dog detection and image cropping.

DINOv2 for visual feature extraction.

FAISS for similarity-based vector retrieval.

The database, uploaded report images, datasets, and downloaded model files are maintained locally and are not included in the Git repository.
