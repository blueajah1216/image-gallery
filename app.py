from flask import Flask, render_template, send_from_directory, abort, request, redirect, url_for
import shutil
import os

app = Flask(__name__)
STATIC_DIR = 'static'

@app.route('/')
def animal_index():
    animals = ['e', 'everything', 'h', 'nn']
    return render_template('animal_index.html', animals=animals)

@app.route('/favorites')
def show_favorites():
    fav_path = os.path.join(STATIC_DIR, 'favorites')
    if not os.path.isdir(fav_path):
        return render_template('index.html', folders=[], animal="favorites")

    folders = [{
        'name': 'favorites',  # used for /board/favorites
        'thumbnail': f"favorites/{img}",
        'label': img
    } for img in sorted(os.listdir(fav_path)) if img.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]

    return render_template('index.html', folders=folders, animal="favorites")

@app.route('/favorite', methods=['POST'])
def favorite():
    rel_path = request.form.get('image_path')
    if not rel_path:
        abort(400)

    src_path = os.path.join(STATIC_DIR, rel_path)
    fav_dir = os.path.join(STATIC_DIR, 'favorites')
    os.makedirs(fav_dir, exist_ok=True)

    filename = os.path.basename(rel_path)
    dest_path = os.path.join(fav_dir, filename)

    # Avoid overwriting favorites with same filename
    if not os.path.exists(dest_path):
        shutil.copy2(src_path, dest_path)

    # Redirect back to the page the user came from
    referer = request.headers.get("Referer", "/")
    return redirect(referer)

@app.route('/all-galleries')  # Optional: keep the original index if you want
def full_gallery_index():
    folders = []
    for folder_name in sorted(os.listdir(STATIC_DIR)):
        folder_path = os.path.join(STATIC_DIR, folder_name)
        if os.path.isdir(folder_path):
            for file_name in sorted(os.listdir(folder_path)):
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    folders.append({
                        'name': folder_name,
                        'thumbnail': f"{folder_name}/{file_name}"
                    })
                    break
    return render_template('index.html', folders=folders)

@app.route('/<animal>')
def animal_gallery(animal):
    base_path = os.path.join(STATIC_DIR, animal)
    if not os.path.isdir(base_path):
        abort(404)

    folders = []
    for folder_name in sorted(os.listdir(base_path)):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            for file_name in sorted(os.listdir(folder_path)):
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    folders.append({
                        'name': f"{animal}/{folder_name}",
                        'thumbnail': f"{animal}/{folder_name}/{file_name}",
                        'label': folder_name
                    })
                    break

    return render_template('index.html', folders=folders, animal=animal)

@app.route('/board/<path:board_name>')
def board(board_name):
    board_path = os.path.join(STATIC_DIR, board_name)
    if not os.path.exists(board_path):
        abort(404)

    images = []
    for file_name in sorted(os.listdir(board_path)):
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            images.append(file_name)

    # Extract animal name (e.g., "bear" from "bear/cute-bears")
    animal = board_name.split('/')[0] if '/' in board_name else None

    return render_template('board.html', board_name=board_name, images=images, animal=animal)

@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory(STATIC_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)