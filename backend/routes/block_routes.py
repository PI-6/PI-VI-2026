from flask import Blueprint, g

from routes.guards import role_required
from routes.helpers import services

bp = Blueprint("blocks", __name__, url_prefix="/api/bloqueios")


# Remover bloqueio (#18): o admin só remove os da própria agenda; o gerente, qualquer um
@bp.delete("/<int:block_id>")
@role_required("admin")
def delete_block(block_id):
    services().blocks.delete_block(block_id, g.current_user)
    return "", 204
