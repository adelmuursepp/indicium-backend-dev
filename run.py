from dotenv import load_dotenv

load_dotenv()

from api import app
from auth_api import auth_api
from courses_api import courses_api
from assignments_api import assignments_api
from groups_api import groups_api
from survey_api import survey_api

app.register_blueprint(survey_api)
app.register_blueprint(auth_api)
app.register_blueprint(courses_api)
app.register_blueprint(assignments_api)
app.register_blueprint(groups_api)

if __name__ == "__main__":
    app.run(debug=True)
