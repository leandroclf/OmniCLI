from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from omnicli import __version__
from omnicli.adapters.subprocess import SubprocessAdapter
from omnicli.config import load_config, write_example_config
from omnicli.diagnostics import diagnose
from omnicli.exceptions import OmniCLIError
from omnicli.lab import LabResult, run_provider_contract_lab, run_synthetic_evaluation
from omnicli.pipeline import PipelineRunner
from omnicli.planning import build_execution_plan

app = typer.Typer(help="Orquestrador local de ferramentas de IA via CLI.")
providers_app = typer.Typer(help="Diagnóstico dos provedores configurados.")
run_app = typer.Typer(help="Inspeção e retomada de execuções.")
lab_app = typer.Typer(help="Verificações determinísticas sem autenticação de provedores.")
app.add_typer(providers_app, name="providers")
app.add_typer(run_app, name="run")
app.add_typer(lab_app, name="lab")
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Valida a configuração e exibe o plano sem executar CLIs ou criar artefatos.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Emite o plano em JSON; aplicável ao modo --dry-run.",
    ),
    refine: bool = typer.Option(
        False,
        "--refine",
        help="Ativa o loop condicional de qualidade; --loops define o máximo de passagens.",
    ),
) -> None:
    """Transforma uma ideia em uma proposta arquitetural consolidada."""
    try:
        loaded = load_config(config)
        if dry_run:
            plan = build_execution_plan(loaded, idea, loops, refine=True if refine else None)
            if output_json:
                console.print_json(json.dumps(plan, ensure_ascii=False))
            else:
                console.print("[cyan]Plano offline; nenhum provedor será executado.[/cyan]")
                table = Table("Campo", "Valor")
                for key, value in plan.items():
                    table.add_row(key, ", ".join(value) if isinstance(value, list) else str(value))
                console.print(table)
            return
        runner = _runner(config, verbose)
        final_path, run_workspace, report = runner.run(
            idea=idea,
            loops=loops,
            output=output,
            workspace_root=workspace,
            refine=True if refine else None,
        )
    except (OmniCLIError, ValueError) as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Concluído:[/green] {final_path}")
    console.print(f"Workspace: {run_workspace.path}")
    console.print(f"Qualidade preliminar: {report.score}/100")
    manifest = run_workspace.load_manifest()
    if manifest.termination_reason:
        console.print(f"Término: {manifest.termination_reason.value}")
    for warning in report.warnings:
        console.print(f"[yellow]Aviso:[/yellow] {warning}")
    if preview:
        console.print(Markdown(final_path.read_text(encoding="utf-8")))


@providers_app.command("check")
def providers_check(
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    capabilities: bool = typer.Option(
        False,
        "--capabilities",
        help="Também verifica marcadores documentados na saída de ajuda da CLI.",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Valida apenas a configuração; não consulta executáveis, versões ou autenticação.",
    ),
) -> None:
    """Verifica quais CLIs estão instaladas e respondendo."""
    try:
        loaded = load_config(config)
    except (OmniCLIError, ValueError) as exc:
        console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    report = diagnose(loaded, check_versions=True, check_capabilities=capabilities, offline=offline)
    table = Table("Provedor", "Comando", "Disponível", "Versão/diagnóstico", "Contrato")
    for provider in report.providers:
        table.add_row(
            provider.name,
            provider.command,
            "sim" if provider.status == "ready" else "não",
            provider.detail,
            provider.capability_status or "não verificado",
        )
    console.print(table)
    if not report.ready:
        raise typer.Exit(code=1)


@app.command()
def doctor(
    config: Path | None = typer.Option(None, "--config", "-c", help="Arquivo YAML de configuração."),
    output_json: bool = typer.Option(False, "--json", help="Emite diagnóstico estruturado em JSON."),
    skip_version: bool = typer.Option(False, "--skip-version", help="Não executa os comandos de versão."),
    capabilities: bool = typer.Option(
        False,
        "--capabilities",
        help="Verifica a superfície de ajuda e o contrato declarado de cada CLI.",
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Valida apenas a configuração; não consulta executáveis, versões ou autenticação.",
    ),
) -> None:
    """Valida configuração, transporte de prompts e CLIs exigidas pelo pipeline."""
    try:
        report = diagnose(
            load_config(config),
            check_versions=not skip_version,
            check_capabilities=capabilities,
            offline=offline,
        )
    except OmniCLIError as exc:
        if output_json:
            console.print_json(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False))
        else:
            console.print(f"[red]Erro:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if output_json:
        console.print_json(json.dumps(report.as_dict(), ensure_ascii=False))
    else:
        table = Table("Provedor", "Obrigatório", "Transporte", "Status", "Versão/diagnóstico", "Contrato")
        for provider in report.providers:
            table.add_row(
                provider.name,
                "sim" if provider.required else "não",
                provider.transport,
                provider.status,
                provider.detail,
                provider.capability_status or "não verificado",
            )
        console.print(table)
        if report.ready:
            if report.mode == "offline":
                console.print("[green]Configuração válida; prontidão real dos provedores não foi testada.[/green]")
            else:
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
    idea: str | None = typer.Option(
        None,
        "--idea",
        help="Ideia original quando a execução foi configurada para não persistir conteúdo.",
    ),
    allow_config_change: bool = typer.Option(
        False,
        "--allow-config-change",
        help="Permite retomar com configuração diferente após revisão manual.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Exibe detalhes da execução."),
) -> None:
    """Retoma a primeira etapa incompleta de uma execução."""
    try:
        runner = _runner(config, verbose)
        final_path, run_workspace, report = runner.resume(
            run_id=run_id,
            output=output,
            workspace_root=workspace,
            idea=idea,
            allow_config_change=allow_config_change,
        )
    except (OmniCLIError, ValueError) as exc:
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
    output_json: bool = typer.Option(False, "--json", help="Emite o manifesto estruturado em JSON."),
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
    if output_json:
        payload = manifest.model_dump(mode="json")
        payload["workspace"] = str(Workspace(root, run_id=run_id).path)
        console.print_json(json.dumps(payload, ensure_ascii=False))
        return

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
    fingerprint = manifest.config_fingerprint[:12] if manifest.config_fingerprint else "-"
    console.print(
        f"Grafo: {manifest.graph_version} | chamadas={manifest.calls_used} | "
        f"configuração={fingerprint}"
    )
    if manifest.execution_mode == "refinement":
        best_score = manifest.best_quality_score if manifest.best_quality_score is not None else "-"
        console.print(
            f"Modo: refinamento | qualidade={best_score} | "
            f"passagens={manifest.passes_completed}/{manifest.total_loops} | "
            f"passos={manifest.steps_used} | "
            f"término={manifest.termination_reason.value if manifest.termination_reason else '-'}"
        )
    console.print(table)


def _print_lab_results(title: str, results: tuple[LabResult, ...]) -> bool:
    table = Table("Caso", "Status", "Detalhe")
    passed = True
    for case in results:
        ok = case.passed
        table.add_row(case.name, "PASS" if ok else "FAIL", case.detail)
        passed = passed and ok
    console.print(f"[bold]{title}[/bold]")
    console.print(table)
    return passed


@lab_app.command("providers")
def lab_providers(
    output_json: bool = typer.Option(False, "--json", help="Emite o resultado estruturado em JSON."),
) -> None:
    """Valida transporte e limites com um provedor sintético local."""
    results = run_provider_contract_lab()
    if output_json:
        payload = {
            "passed": all(result.passed for result in results),
            "results": [result.as_dict() for result in results],
        }
        console.print_json(json.dumps(payload, ensure_ascii=False))
    elif not _print_lab_results("Laboratório de contratos de provedores", results):
        raise typer.Exit(code=1)
    if not all(result.passed for result in results):
        raise typer.Exit(code=1)


@lab_app.command("evaluate")
def lab_evaluate(
    output_json: bool = typer.Option(False, "--json", help="Emite o resultado estruturado em JSON."),
) -> None:
    """Executa a regressão sintética do avaliador quality-v1."""
    results = run_synthetic_evaluation()
    if output_json:
        payload = {
            "passed": all(result.passed for result in results),
            "results": [result.as_dict() for result in results],
        }
        console.print_json(json.dumps(payload, ensure_ascii=False))
    elif not _print_lab_results("Regressão sintética de qualidade", results):
        raise typer.Exit(code=1)
    if not all(result.passed for result in results):
        raise typer.Exit(code=1)


@lab_app.command("verify")
def lab_verify(
    output_json: bool = typer.Option(False, "--json", help="Emite o resultado estruturado em JSON."),
) -> None:
    """Executa todas as verificações locais que não exigem autenticação."""
    provider_results = run_provider_contract_lab()
    evaluation_results = run_synthetic_evaluation()
    result = {
        "provider_contracts": [item.as_dict() for item in provider_results],
        "synthetic_evaluation": [item.as_dict() for item in evaluation_results],
        "passed": all(item.passed for item in provider_results + evaluation_results),
        "authenticated_provider_compatibility": "not-tested",
        "human_quality_benchmark": "not-tested",
    }
    if output_json:
        console.print_json(json.dumps(result, ensure_ascii=False))
    else:
        providers_ok = _print_lab_results("Laboratório de contratos de provedores", provider_results)
        evaluation_ok = _print_lab_results("Regressão sintética de qualidade", evaluation_results)
        console.print(
            "Compatibilidade autenticada: não testada | Benchmark humano: não testado"
        )
        if not (providers_ok and evaluation_ok):
            raise typer.Exit(code=1)
    if not bool(result["passed"]):
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Exibe a versão do OmniCLI."""
    console.print(__version__)
