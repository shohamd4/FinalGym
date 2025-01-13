import streamlit as st
from datetime import datetime, timedelta
from peewee import *

# Database setup
db = SqliteDatabase('gym.db')

# Models
class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = AutoField()
    name = CharField()
    email = CharField(unique=True)
    registration_week = DateField(null=True)

class Lesson(BaseModel):
    id = AutoField()
    datetime = DateTimeField()
    capacity = IntegerField(default=6)

class Registration(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref='registrations')
    lesson = ForeignKeyField(Lesson, backref='registrations')
    timestamp = DateTimeField(default=datetime.utcnow)

# Initialize the database
db.connect()
db.create_tables([User, Lesson, Registration])

# Helper functions
def get_lessons():
    lessons = Lesson.select()
    result = []
    for lesson in lessons:
        registrations = Registration.select().where(Registration.lesson == lesson).count()
        result.append({
            'id': lesson.id,
            'datetime': lesson.datetime,
            'available_slots': lesson.capacity - registrations
        })
    return result

def get_future_lessons():
    now = datetime.utcnow()
    lessons = Lesson.select().where(Lesson.datetime > now)
    result = []
    for lesson in lessons:
        registrations = Registration.select().where(Registration.lesson == lesson).count()
        result.append({
            'id': lesson.id,
            'datetime': lesson.datetime,
            'available_slots': lesson.capacity - registrations
        })
    return result

def register_user(user_id, lesson_id):
    try:
        user = User.get_by_id(user_id)
        lesson = Lesson.get_by_id(lesson_id)
    except DoesNotExist:
        return 'Invalid user or lesson ID'

    start_of_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    if user.registration_week and user.registration_week >= start_of_week.date():
        return 'User already registered this week'

    registrations = Registration.select().where(Registration.lesson == lesson).count()
    if registrations >= lesson.capacity:
        return 'Lesson is full'

    if datetime.utcnow() < lesson.datetime - timedelta(hours=12):
        return 'Registration only allowed 12 hours before the lesson'

    Registration.create(user=user, lesson=lesson)
    user.registration_week = start_of_week.date()
    user.save()

    return 'Registration successful'

def initialize_data():
    User.create(name='Alice', email='alice@example.com')
    User.create(name='Bob', email='bob@example.com')

    lesson1_time = datetime.utcnow() + timedelta(days=1, hours=3)
    lesson2_time = datetime.utcnow() + timedelta(days=2)
    Lesson.create(datetime=lesson1_time)
    Lesson.create(datetime=lesson2_time)

def add_lesson(lesson_datetime, capacity):
    try:
        Lesson.create(datetime=lesson_datetime, capacity=capacity)
        return 'Lesson added successfully'
    except Exception as e:
        return f'Error adding lesson: {e}'

# Streamlit UI
st.title("Gym Lesson Registration")

# Initialize data if required
if st.button('Initialize Data'):
    initialize_data()
    st.success("Sample data initialized")

# Show lessons
st.header("Available Lessons")
lessons = get_lessons()
for lesson in lessons:
    st.write(f"Lesson ID: {lesson['id']}, DateTime: {lesson['datetime']}, Available Slots: {lesson['available_slots']}")

# Show future lessons
st.header("Future Lessons")
future_lessons = get_future_lessons()
for lesson in future_lessons:
    st.write(f"Lesson ID: {lesson['id']}, DateTime: {lesson['datetime']}, Available Slots: {lesson['available_slots']}")

# Registration form
st.header("Register for a Lesson")
user_id = st.number_input("Enter your User ID", min_value=1, step=1)
lesson_id = st.number_input("Enter the Lesson ID", min_value=1, step=1)
if st.button("Register"):
    message = register_user(user_id, lesson_id)
    st.info(message)

# Add lesson form
st.header("Add a New Lesson (Admin Only)")
new_lesson_date = st.date_input("Select lesson date")
new_lesson_time = st.time_input("Select lesson time")
new_lesson_capacity = st.number_input("Enter lesson capacity", min_value=1, step=1)
if st.button("Add Lesson"):
    lesson_datetime = datetime.combine(new_lesson_date, new_lesson_time)
    message = add_lesson(lesson_datetime, new_lesson_capacity)
    st.info(message)
