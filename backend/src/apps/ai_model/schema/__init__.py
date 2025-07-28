"""
AI Model schemas
"""

from .ai_model import (
    AIModelCreate, AIModelUpdate, AIModelResponse, AIModelQueryParams,
    AIModelTestRequest, AIModelTestResponse, AIModelStatusUpdate,
    OllamaDiscoverRequest, OllamaDiscoverResponse
)

__all__ = [
    'AIModelCreate', 'AIModelUpdate', 'AIModelResponse', 'AIModelQueryParams',
    'AIModelTestRequest', 'AIModelTestResponse', 'AIModelStatusUpdate',
    'OllamaDiscoverRequest', 'OllamaDiscoverResponse'
]