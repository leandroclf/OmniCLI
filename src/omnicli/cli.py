from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from omnicli import __version__
from omnicli.adapters.subprocess import SubprocessAdapter, command_exists
from omnicli.config import load_config, write_example_config
from omnicli.diagnostics import diagnose
from omnicli.exceptions import OmniCLIError
from omnicli.pipeline import PipelineRunner

app = typer.Typer(help="Orquestrador local de ferramentas de IA via CLI.")
providers_app = typer.Typer(help="Diagnóstico dos provedores configurados.")
run_app = typer.Typer(help="Inspeção e retomada de execuções.")
app.add_typer(providers_app, name="providers")
app.add_typer(run_app, name="run")
console = Console()


def _runner(config_path: Path | None, verbose: bool) -> PipelineRunner:
    config = load_config(config_path)
    adapters = {name: SubprocessAdapter(name, provider_config) for name, provider_config in config.providers.items()}
    logger = console.print if verbose else None
    return PipelineRunner(config, adapters, logger=logger)


@app.command()
def conceive(
    idea: str = typer.Argument(..., help="Ideia inicial do projeto."),
    loops: int = typer.Option(1, "--loops", "-l", min=1, help="Quantidade de ciclos completos."),
    output: Path = typer.Option(Path("proposta.md"), "--output", "-o", help="Arquivo Markdown final."),
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    workspace: Path | None = typer.Option(None, "--workspace", help="Diretório para artefatos."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Exibe detalhes da execução."),
    preview: bool = typer.Option(False, "--preview", help="Exibe o documento final no terminal."),
) -> None:
    """Transforma uma ideia em uma proposta arquitetural consolidada."""
    try:
        runner = _runner(config, verbose)
        final_path, run_workspace, report = runner.run(
            idea=idea,
            loops=loops,
            output=output,
            workspace_root=workspace,
        )
    except OmniCLIError as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Concluído:[/green] {final_path}")
    console.print(f"Workspace: {run_workspace.path}")
    console.print(f"Qualidade preliminar: {report.score}/100")
    for warning in report.warnings:
        console.print(f"[yellow]Aviso:[/yellow] {warning}")
    if preview:
        console.print(Markdown(final_path.read_text(encoding="utf-8")))


@providers_app.command("check")
def providers_check(
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
) -> None:
    """Verifica quais CLIs estão instaladas e respondendo."""
    try:
        loaded = load_config(config)
    except OmniCLIError as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    table = Table("Provedor", "Comando", "Disponível", "Versão/diagnóstico")
    for name, provider_config in loaded.providers.items():
        if not provider_config.enabled:
            table.add_row(name, provider_config.command, "não", "desabilitado")
            continue
        if not command_exists(provider_config.command):
            table.add_row(name, provider_config.command, "não", "comando não encontrado")
            continue
        try:
            version = SubprocessAdapter(name, provider_config).check()
            table.add_row(name, provider_config.command, "sim", version)
        except OmniCLIError as exc:
            table.add_row(name, provider_config.command, "não", str(exc))
    console.print(table)


@app.command()
def doctor(
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    output_json: bool = typer.Option(False, "--json", help="Emite diagnóstico estruturado em JSON."),
    skip_version: bool = typer.Option(False, "--skip-version", help="Não executa os comandos de versão."),
) -> None:
    """Valida configuração, transporte de prompts e CLIs exigidas pelo pipeline."""
    try:
        report = diagnose(load_config(config), check_versions=not skip_version)
    except OmniCLIError as exc:
        if output_json:
            console.print_json(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False))
        else:
            console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if output_json:
        console.print_json(json.dumps(report.as_dict(), ensure_ascii=False))
    else:
        table = Table("Provedor", "Obrigatório", "Transporte", "Status", "Detalhe")
        for provider in report.providers:
            table.add_row(
                provider.name,
                "sim" if provider.required else "não",
                provider.transport,
                provider.status,
                provider.detail,
            )
        console.print(table)
        if report.ready:
            console.print("[green]Ambiente pronto para o pipeline configurado.[/green]")
        else:
            console.print("[red]Ambiente ainda não está pronto.[/red]")
    if not report.ready:
        raise typer.Exit(code=1)


@app.command("init")
def init_config(
    path: Path = typer.Argument(Path("omnicli.yaml"), help="Arquivo a ser criado."),
) -> None:
    """Cria uma configuração inicial editável."""
    if path.exists() and not typer.confirm(f"Sobrescrever {path}?"):
        raise typer.Abort()
    write_example_config(path)
    console.print(f"Configuração criada em {path}")


@run_app.command("resume")
def resume_run(
    run_id: str = typer.Argument(..., help="Identificador da execução no workspace."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Arquivo Markdown final."),
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    workspace: Path | None = typer.Option(None, "--workspace", help="Diretório dos artefatos."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Exibe detalhes da execução."),
) -> None:
    """Retoma a primeira etapa incompleta de uma execução."""
    try:
        runner = _runner(config, verbose)
        final_path, run_workspace, report = runner.resume(
            run_id=run_id,
            output=output,
            workspace_root=workspace,
        )
    except OmniCLIError as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Retomado e concluído:[/green] {final_path}")
    console.print(f"Workspace: {run_workspace.path}")
    console.print(f"Qualidade preliminar: {report.score}/100")


@run_app.command("inspect")
def inspect_run(
    run_id: str = typer.Argument(..., help="Identificador da execução no workspace."),
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    workspace: Path | None = typer.Option(None, "--workspace", help="Diretório dos artefatos."),
) -> None:
    """Exibe o manifesto de uma execução."""
    try:
        loaded = load_config(config)
        root = workspace or loaded.pipeline.workspace
        from omnicli.workspace import Workspace

        manifest = Workspace(root, run_id=run_id).load_manifest()
    except (OmniCLIError, OSError, ValueError) as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    table = Table("Loop", "Etapa", "Provedor", "Status", "Saída")
    for result in manifest.stages:
        table.add_row(
            str(result.loop),
            result.stage,
            result.provider,
            result.status.value,
            result.output_file or result.error or "-",
        )
    console.print(f"Execução: {manifest.run_id} | status={manifest.status.value}")
    console.print(table)


@app.command()
def version() -> None:
    """Exibe a versão do OmniCLI."""
    console.print(__version__)
