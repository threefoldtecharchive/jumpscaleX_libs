import json
from Jumpscale import j

from .GiteaRepo import GiteaRepo

JSBASE = j.baseclasses.object


class GiteaRepoForNonOwner(GiteaRepo):
    pass
