from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

# -------------------------------------------------------------------
# 1. Setup
# -------------------------------------------------------------------

# Create the FastAPI app instance
app = FastAPI(
    title="My To-Do List API",
    description="A simple API for teaching HTTP methods.",
    version="1.0.0"
)

# In-memory "database" (a simple Python dictionary)
# We will store tasks using their ID as the key.
db_tasks = {}
task_id_counter = 0

# -------------------------------------------------------------------
# 2. Pydantic Models (Data Validation)
# -------------------------------------------------------------------
# These models define the shape of your data.
# FastAPI uses them to validate incoming requests and format responses.

class TaskBase(BaseModel):
    """Base model for a task, contains common fields."""
    title: str
    description: Optional[str] = None
    completed: bool = False

class TaskCreate(TaskBase):
    """Model used when *creating* a new task (via POST)."""
    # No 'id' here, as the server will generate it.
    pass

class TaskUpdate(BaseModel):
    """Model used when *partially updating* a task (via PATCH)."""
    # All fields are optional for a partial update.
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Task(TaskBase):
    """Model used when *reading* a task (the full task object)."""
    # This model includes the 'id' that the server assigns.
    id: int

# -------------------------------------------------------------------
# 3. API Endpoints (HTTP Methods)
# -------------------------------------------------------------------

@app.get("/")
def read_root():
    """A simple root endpoint to welcome users."""
    return {"message": "Welcome to the To-Do List API!"}

# --- CREATE ---

@app.post("/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate):
    """
    CREATE a new task.
    - Uses HTTP POST.
    - Receives a 'TaskCreate' model in the request body.
    - Returns the newly created 'Task' model with an ID.
    """
    global task_id_counter
    task_id_counter += 1
    
    # Create the full Task object, including the new ID
    new_task = Task(id=task_id_counter, **task_in.dict())
    
    # Save to our "database"
    db_tasks[new_task.id] = new_task
    
    return new_task

# --- READ (All) ---

@app.get("/tasks/", response_model=List[Task])
def get_all_tasks():
    """
    READ all tasks.
    - Uses HTTP GET.
    - Returns a list of 'Task' models.
    """
    return list(db_tasks.values())

# --- READ (One) ---

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    """
    READ a single task by its ID.
    - Uses HTTP GET.
    - Uses a 'path parameter' (task_id) to identify the resource.
    - Returns a single 'Task' model.
    """
    task = db_tasks.get(task_id)
    if not task:
        # If the task doesn't exist, raise a 404 Not Found error.
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# --- UPDATE (Full) ---

@app.put("/tasks/{task_id}", response_model=Task)
def update_task_full(task_id: int, task_in: TaskCreate):
    """
    UPDATE a task completely (full replacement).
    - Uses HTTP PUT.
    - Replaces the existing task with the new data.
    - Requires all fields (except id) to be sent in the body.
    """
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create a new Task object with the provided data and the existing ID
    updated_task = Task(id=task_id, **task_in.dict())
    db_tasks[task_id] = updated_task
    
    return updated_task

# --- UPDATE (Partial) ---

@app.patch("/tasks/{task_id}", response_model=Task)
def update_task_partial(task_id: int, task_in: TaskUpdate):
    """
    UPDATE a task partially.
    - Uses HTTP PATCH.
    - Only updates the fields provided in the request body.
    """
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    existing_task = db_tasks[task_id]
    
    # Create a dictionary of the fields to update
    # 'exclude_unset=True' is key: it only includes fields
    # that were actually sent in the request.
    update_data = task_in.dict(exclude_unset=True)
    
    # Update the existing task object with the new data
    updated_task = existing_task.copy(update=update_data)
    
    db_tasks[task_id] = updated_task
    return updated_task

# --- DELETE ---

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    """
    DELETE a task by its ID.
    - Uses HTTP DELETE.
    - Returns a 204 No Content status code on success.
    """
    if task_id not in db_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del db_tasks[task_id]
    
    # A 204 response should not have a body, so we return None.
    return None