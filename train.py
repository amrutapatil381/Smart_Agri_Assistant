import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import os


# Define dataset transformations
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])

# Load dataset
train_dataset = datasets.ImageFolder(root="PlantVillage/train", transform=transform)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Define CNN Model
# Count the actual number of classes in your dataset
num_classes = len(os.listdir("PlantVillage/train"))
class PlantDiseaseModel(nn.Module):
    def __init__(self, num_classes=num_classes):
        super(PlantDiseaseModel, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2, padding=0)

        self._to_linear = None
        self._get_flattened_size()

        self.fc1 = nn.Linear(self._to_linear, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def _get_flattened_size(self):
        with torch.no_grad():
            x = torch.randn(1, 3, 128, 128)
            x = self.pool(self.relu(self.conv1(x)))
            self._to_linear = x.view(1, -1).size(1)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x



# Initialize model, loss function, and optimizer
model = PlantDiseaseModel()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
num_epochs = 5
for epoch in range(num_epochs):
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        if batch_idx % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Batch [{batch_idx+1}/{len(train_loader)}], Loss: {loss.item()}")

# Save the new trained model
torch.save(model.state_dict(), "plant_disease_model.pth")
print("🎉 Training complete. Model saved as 'plant_disease_model.pth'.")
