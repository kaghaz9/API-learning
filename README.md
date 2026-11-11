# Task Manager API

A simple REST API built with Flask and SQLite. This is a learning project.

## Features

- Create, read, update and delete tasks
- Optional image upload for each task
- Input validation with clear JSON error messages

## Setup

```
python -m pip install -r requirements.txt
python app.py
```

The server runs at http://127.0.0.1:5000

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/tasks` | List all tasks |
| GET | `/tasks/<id>` | Get one task |
| POST | `/tasks` | Create a task (form-data: `title`, optional `image`) |
| PUT | `/tasks/<id>` | Update a task (JSON: `title`, `done`) |
| DELETE | `/tasks/<id>` | Delete a task |
| GET | `/uploads/<filename>` | Get an uploaded image |

## Example response

```json
{
  "id": 1,
  "title": "Buy bread",
  "done": false,
  "image_filename": null,
  "image_url": null
}
```