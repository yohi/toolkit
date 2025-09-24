"""Machine learning module for CodeRabbit fetcher."""

from .comment_classifier import (
    ClassificationModel,
    CommentFeatures,
    MLCommentClassifier,
    ModelMetrics,
    TrainingData,
)
from .ensemble_classifier import EnsembleClassifier, StackingClassifier, WeightedVoting
from .feature_extractor import CommentFeatureSet, ContextFeatures, FeatureExtractor, TextFeatures
from .model_trainer import ModelEvaluator, ModelTrainer, TrainingConfig, ValidationResult

__all__ = [
    # Main Classifier
    "MLCommentClassifier",
    "CommentFeatures",
    "ClassificationModel",
    "TrainingData",
    "ModelMetrics",
    # Feature Extraction
    "FeatureExtractor",
    "TextFeatures",
    "ContextFeatures",
    "CommentFeatureSet",
    # Model Training
    "ModelTrainer",
    "TrainingConfig",
    "ValidationResult",
    "ModelEvaluator",
    # Ensemble Methods
    "EnsembleClassifier",
    "WeightedVoting",
    "StackingClassifier",
]
