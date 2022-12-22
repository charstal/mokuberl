import torch
import torch.nn as nn


class QNetWork(nn.Module):
    def __init__(self, state_size, action_size, seed):

        super(QNetWork, self).__init__()
        self.seed = torch.manual_seed(seed)
        self.network = nn.Sequential(
            nn.Linear(state_size, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
            # nn.Linear(state_size, 120),
            # nn.ReLU(),
            # nn.Linear(120, 84),
            # nn.ReLU(),
            # nn.Linear(84, action_size),
        )

    def forward(self, x):
        return self.network(x)
