from app.db.session import Base

# Importer ici tous les modèles pour que Base.metadata.create_all() fonctionne
from app.models import user, cv
