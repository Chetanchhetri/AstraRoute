import torch
from torch import nn

class MultiTaskWeatherNowcaster(nn.Module):
    """Placeholder architecture for the production package.

    Replace this architecture with the exact architecture used to train
    the supplied checkpoint before loading its state_dict.
    """

    def __init__(self, tabular_input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.image_encoder = nn.Sequential(
            nn.Flatten(),
            nn.Linear(3 * 224 * 224, hidden_dim),
            nn.ReLU(),
        )
        self.tabular_encoder = nn.Sequential(
            nn.Linear(tabular_input_dim, hidden_dim),
            nn.ReLU(),
        )
        self.shared = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
        )
        self.onset_class = nn.Linear(hidden_dim, 4)
        self.intensity = nn.Linear(hidden_dim, 1)
        self.duration = nn.Linear(hidden_dim, 1)
        self.impact_bbox = nn.Linear(hidden_dim, 4)

    def forward(self, image, tabular):
        image_features = self.image_encoder(image)
        tabular_features = self.tabular_encoder(tabular)
        features = self.shared(torch.cat([image_features, tabular_features], dim=1))
        return {
            "onset_class": self.onset_class(features),
            "intensity": self.intensity(features),
            "duration": self.duration(features),
            "impact_bbox": self.impact_bbox(features),
        }
