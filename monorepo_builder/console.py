import click


def write_to_console(message, color=None, bold=False):
    if color:
        click.secho(message, fg=color, bold=bold)
    elif bold:
        click.secho(message, bold=True)
    else:
        click.echo(message)
