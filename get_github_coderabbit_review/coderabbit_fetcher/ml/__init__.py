"""Machine learning module for CodeRabbit fetcher."""

from .comment_classifier import (
    MLCommentClassifier,
    CommentFeatures,
    ClassificationModel,
    TrainingData,
    ModelMetrics
)

from .feature_extractor import (
    FeatureExtractor,
    TextFeatures,
    ContextFeatures,
    CommentFeatureSet
)

from .model_trainer import (
    ModelTrainer,
    TrainingConfig,
    ValidationResult,
    ModelEvaluator
)

from .ensemble_classifier import (
    EnsembleClassifier,
    WeightedVoting,
    StackingClassifier
)

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
    "StackingClassifier"
]
