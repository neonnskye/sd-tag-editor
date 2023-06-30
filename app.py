import os
import datetime
import zipfile
import shutil
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    after_this_request,
)

app = Flask(__name__)


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


@app.route("/")
def index():
    return render_template("index.html", dataset_metadata=get_dataset_metadata())


@app.route("/edit/<dataset_name>")
def edit(dataset_name):
    _, image_dir, caption_dir = get_dataset_dirs(dataset_name)
    image_filenames = os.listdir(image_dir)
    captions = []
    for caption_filename in os.listdir(caption_dir):
        with open(os.path.join(caption_dir, caption_filename), "r") as f:
            captions.append(f.read())
    image_caption_data = []
    for image_filename, caption in zip(image_filenames, captions):
        image_caption_data.append(
            {"image_filename": image_filename, "caption": caption}
        )
    return render_template(
        "edit.html", dataset_name=dataset_name, image_caption_data=image_caption_data
    )


@app.route("/submit/<dataset_name>", methods=["POST"])
def submit(dataset_name):
    _, _, caption_dir = get_dataset_dirs(dataset_name)
    for filename, caption in request.form.items():
        filename = os.path.splitext(filename)[0] + ".txt"
        with open(os.path.join(caption_dir, filename), "w") as f:
            f.write(caption.strip())
    return redirect(url_for("edit", dataset_name=dataset_name))


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    filename = file.filename
    if os.path.splitext(filename)[1] != ".zip":
        return "Invalid file"

    file_save_path = os.path.join("transfers", filename)
    file.save(file_save_path)
    dest_dataset_name = os.path.splitext(filename)[0]
    dest_dataset_dir = "static/data/" + dest_dataset_name

    if os.path.exists(dest_dataset_dir):
        counter = 2  # Start counter from 2
        while os.path.exists(dest_dataset_dir):
            # Append a counter to the filename to handle duplicates
            dest_dataset_name = f"{os.path.splitext(filename)[0]} ({counter})"
            dest_dataset_dir = "static/data/" + dest_dataset_name
            counter += 1

    os.makedirs(dest_dataset_dir + "/images")
    os.makedirs(dest_dataset_dir + "/text")
    with zipfile.ZipFile(file_save_path, "r") as zipf:
        zipf.extractall(dest_dataset_dir)
    for file_path in os.listdir(dest_dataset_dir):
        if os.path.isfile(os.path.join(dest_dataset_dir, file_path)):
            if "txt" in os.path.splitext(file_path)[1]:
                shutil.move(
                    os.path.join(dest_dataset_dir, file_path),
                    os.path.join(dest_dataset_dir, "text", file_path),
                )
            else:
                shutil.move(
                    os.path.join(dest_dataset_dir, file_path),
                    os.path.join(dest_dataset_dir, "images", file_path),
                )

    os.remove(file_save_path)
    return dest_dataset_name


@app.route("/download/<dataset_name>")
def download(dataset_name):
    transfer_folder = os.path.join("transfers", dataset_name)
    os.makedirs(transfer_folder)
    zip_file = os.path.join(transfer_folder, f"{dataset_name}.zip")
    _, _, caption_dir = get_dataset_dirs(dataset_name)
    for file in os.listdir(caption_dir):
        shutil.copy2(
            os.path.join(caption_dir, file), os.path.join(transfer_folder, file)
        )
    with zipfile.ZipFile(zip_file, "w") as zipf:
        for file in os.listdir(transfer_folder):
            if file == os.path.basename(zip_file):
                continue
            zipf.write(os.path.join(transfer_folder, file), file)

    @after_this_request
    def cleanup(response):
        shutil.rmtree(transfer_folder)
        return response

    return send_file(zip_file, as_attachment=True)


@app.route("/delete/<dataset_name>")
def delete(dataset_name):
    return render_template("delete.html", dataset_name=dataset_name)


@app.route("/delete/<dataset_name>/confirm", methods=["POST"])
def delete_confirm(dataset_name):
    shutil.rmtree(os.path.join("static/data", dataset_name))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
