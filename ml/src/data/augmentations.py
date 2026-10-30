from torchvision import transforms


# Augmentation for training images only
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ToTensor()
])


# No augmentation for validation and test images
eval_transform = transforms.Compose([
    transforms.ToTensor()
])