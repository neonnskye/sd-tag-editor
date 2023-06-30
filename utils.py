import os
import datetime


def get_dataset_metadata():
    dataset_metadata = []
    dataset_names = os.listdir("static/data")
    for dataset_name in dataset_names:
        dataset_dir, image_dir, caption_dir = get_dataset_dirs(dataset_name)
        dataset_created_time = os.path.getctime(dataset_dir)
        dataset_modified_time = 0
        for caption_filename in os.listdir(caption_dir):
            file_modified_time = os.path.getmtime(
                os.path.join(caption_dir, caption_filename)
            )
            if file_modified_time > dataset_modified_time:
                dataset_modified_time = file_modified_time
        if (dataset_modified_time - dataset_created_time) < 1:
            modified_value = "-"
        else:
            modified_value = get_relative_datetime(dataset_modified_time)
        dataset_metadata.append(
            {
                "name": dataset_name,
                "images": len(os.listdir(image_dir)),
                "created": get_relative_datetime(dataset_created_time),
                "modified": modified_value,
            }
        )
    return dataset_metadata


def get_relative_datetime(timestamp):
    current_time = datetime.datetime.now()
    target_time = datetime.datetime.fromtimestamp(timestamp)
    time_difference = current_time - target_time

    if time_difference.total_seconds() < 60:
        return "Just now"
    elif time_difference.total_seconds() < 3600:
        minutes = int(time_difference.total_seconds() / 60)
        if minutes > 1:
            return f"{minutes} minutes ago"
        else:
            return f"{minutes} minute ago"
    elif time_difference.total_seconds() < 86400:
        hours = int(time_difference.total_seconds() / 3600)
        if hours > 1:
            return f"{hours} hours ago"
        else:
            return f"{hours} hour ago"
    else:
        days = time_difference.days
        if days > 1:
            return f"{days} days ago"
        else:
            return f"{days} day ago"


def get_dataset_dirs(dataset_name):
    dataset_dir = os.path.join("static/data", dataset_name)
    image_dir = os.path.join(dataset_dir, "images")
    caption_dir = os.path.join(dataset_dir, "text")
    return dataset_dir, image_dir, caption_dir
