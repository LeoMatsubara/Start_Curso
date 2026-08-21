from canvas_client import CanvasClient

client = CanvasClient()

course_id = client.get_course_id(
    "DPEAD20262.002"
)

print("Course ID:", course_id)

course = client.get(
    f"/courses/{course_id}"
)

print("Status:", course.status_code)

if course.status_code == 200:
    print("Nome:", course.json()["name"])