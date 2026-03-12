from app.db.session import Base
import app.models

# Importer ici tous les modèles pour que Base.metadata.create_all() fonctionne
from app.models import user, cv, job, application, user_job_profile, refresh_token
