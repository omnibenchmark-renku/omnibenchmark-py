from typing import Optional, List
from renku.command.save import save_and_push_command


def renku_save(
    message: Optional[str] = None,
    destination: Optional[str] = None,
    paths: Optional[List[str]] = None,
):

    saved_paths, branch = (
        save_and_push_command()
        .build()
        .execute(message=message, remote=destination, paths=paths)
        .output
    )
    if saved_paths:
        print(
            "Successfully saved to remote branch {}: \n\t{}".format(
                branch, "\n\t".join(saved_paths)
            )
        )
    else:
        print("There were no changes to save.")
