from js import setTimeout
from pyodide.ffi import create_proxy
from pyscript import document

index = 0
rows, cols = 4, 5
matrix = [[i + j * cols for i in range(cols)] for j in range(rows)]
snake = []
for i, row in enumerate(matrix):
    snake += row if i % 2 == 0 else row[::-1]

# Build table
table = document.createElement("table")
table.style.borderCollapse = "collapse"
table.style.fontFamily = "monospace"
table.id = "matrix-table"

for row in matrix:
    tr = document.createElement("tr")
    for val in row:
        td = document.createElement("td")
        td.innerText = str(val)
        td.style.border = "1px solid black"
        td.style.padding = "4px"
        td.style.textAlign = "center"
        td.id = f"cell-{val}"
        tr.appendChild(td)
    table.appendChild(tr)

container = document.getElementById("matrix-container")
container.innerHTML = ""
container.appendChild(table)


# Animate with loop
def animate():
    if not document.getElementById("matrix-container"):
        return
    global index
    # print("index", index)
    if index >= len(snake):
        index = 0  # 🔁 reset for loop
        for val in snake:  # clear styles
            cell = document.getElementById(f"cell-{val}")
            cell.innerText = str(val)
            cell.style.backgroundColor = ""

    val = snake[index]
    cell = document.getElementById(f"cell-{val}")
    cell.style.backgroundColor = "#cfc"
    cell.innerText = "🐍"

    if index > 0:
        prev = snake[index - 1]
        prev_cell = document.getElementById(f"cell-{prev}")
        prev_cell.style.backgroundColor = ""
        prev_cell.innerText = str(prev)

    index += 1
    setTimeout(create_proxy(animate), 500)


animate()
