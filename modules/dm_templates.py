"""Gerador e gerenciador de templates de atendimento (DM e WhatsApp)."""

import json
import re
from datetime import datetime

from modules import ai_client
from utils import display, storage


# ─── Templates base embutidos ─────────────────────────────────────────────────

BUILTIN_TEMPLATES: dict[str, dict] = {
    "orcamento_simples": {
        "category": "Orcamento",
        "channel": "DM / WhatsApp",
        "subject": "Resposta a pedido de orcamento",
        "template": (
            "Oi {nome}! Obrigado pelo interesse no meu trabalho ✌\n\n"
            "Para fazer um orçamento preciso de algumas informações:\n"
            "• Qual região do corpo?\n"
            "• Tamanho aproximado (palma, A4, etc)?\n"
            "• Tem alguma referência visual?\n\n"
            "Me manda essas informações que já te passo os valores! 🖤"
        ),
    },
    "orcamento_detalhado": {
        "category": "Orcamento",
        "channel": "DM / WhatsApp",
        "subject": "Orcamento recebido — solicita referencia",
        "template": (
            "Oi {nome}! Vi sua mensagem 😊\n\n"
            "Trabalho com {estilo} e atendo em {cidade}.\n\n"
            "Para te passar um valor mais preciso, me manda:\n"
            "📍 Local do corpo\n"
            "📐 Tamanho (em cm ou comparando com uma parte do corpo)\n"
            "🖼 Referências visuais (fotos, ideias, estilos que você curtiu)\n\n"
            "Assim consigo te dar uma estimativa real! Aguardo 🤙"
        ),
    },
    "disponibilidade": {
        "category": "Agendamento",
        "channel": "DM / WhatsApp",
        "subject": "Informar disponibilidade de agenda",
        "template": (
            "Oi {nome}! Tudo bem?\n\n"
            "Minha agenda está aberta para {periodo}. "
            "As sessões costumam durar {duracao} dependendo do projeto.\n\n"
            "Se quiser garantir uma data, me manda sua disponibilidade de horários "
            "e a ideia do projeto que você quer fazer! 🖤"
        ),
    },
    "agenda_cheia": {
        "category": "Agendamento",
        "channel": "DM / WhatsApp",
        "subject": "Agenda lotada — lista de espera",
        "template": (
            "Oi {nome}! Obrigado pelo interesse 🙏\n\n"
            "No momento minha agenda está fechada até {data_previsao}.\n\n"
            "Se quiser, posso te adicionar na lista de espera e te aviso assim "
            "que abrir novas datas. Basta me confirmar!\n\n"
            "Me manda também o projeto que você tem em mente, assim já fico "
            "pensando nas possibilidades! 🖤"
        ),
    },
    "confirmacao_sessao": {
        "category": "Pos-venda",
        "channel": "WhatsApp",
        "subject": "Confirmacao de sessao agendada",
        "template": (
            "Oi {nome}! Passando para confirmar sua sessão 🖤\n\n"
            "📅 Data: {data}\n"
            "⏰ Horário: {horario}\n"
            "📍 Local: {endereco}\n\n"
            "Lembretes importantes:\n"
            "✓ Venha bem alimentado(a)\n"
            "✓ Vista roupa confortável que dê acesso à região\n"
            "✓ Evite álcool e anticoagulantes nas 24h anteriores\n"
            "✓ Qualquer dúvida me chama!\n\n"
            "Nos vemos em breve 🤙"
        ),
    },
    "pos_cuidados": {
        "category": "Pos-venda",
        "channel": "WhatsApp",
        "subject": "Instrucoes de cuidados pos-tattoo",
        "template": (
            "Oi {nome}! Tudo bem com a tattoo? 😊\n\n"
            "Segue o protocolo de cuidados:\n\n"
            "📌 Primeiras 3-4 horas: mantenha o curativo\n"
            "🚿 Lavar com sabonete neutro 2x ao dia (suavemente)\n"
            "💧 Aplicar hidratante sem perfume após lavar (Bepantol Baby ou similar)\n"
            "☀️ Evitar sol direto e piscina por 3 semanas\n"
            "🚫 NÃO arranhe, mesmo com coceira — é normal!\n\n"
            "Cicatrização completa: 30-45 dias.\n\n"
            "Qualquer dúvida ou se surgir algo incomum, me chama! 🖤"
        ),
    },
    "referencia_nao_disponivel": {
        "category": "Projeto",
        "channel": "DM / WhatsApp",
        "subject": "Referencia recebida — nao faço esse estilo",
        "template": (
            "Oi {nome}! Obrigado por me procurar 🙏\n\n"
            "Vi a referência que você mandou, mas ela é mais do estilo {estilo_diferente} "
            "e o meu foco é {estilo_proprio}.\n\n"
            "Posso criar algo no meu estilo com uma proposta similar se você topar, "
            "mas caso esteja buscando exatamente essa referência, posso te indicar "
            "alguns artistas que trabalham com isso!\n\n"
            "Me fala o que você prefere? 😊"
        ),
    },
    "follow_up_orcamento": {
        "category": "Follow-up",
        "channel": "DM / WhatsApp",
        "subject": "Follow-up para orcamento sem resposta",
        "template": (
            "Oi {nome}, tudo bem?\n\n"
            "Passando para ver se você teve alguma dúvida sobre o projeto que conversamos 😊\n\n"
            "Se quiser ajustar algo — tamanho, posição, referência — é só falar! "
            "Estou aqui para dar todas as informações que precisar 🖤"
        ),
    },
}


# ─── Prompt para gerar template customizado ──────────────────────────────────


def _build_custom_template_prompt(
    scenario: str,
    tone: str,
    tattoo_style: str,
    artist_name: str,
    artist_city: str,
) -> str:
    tone_desc = {
        "informal": "tom descontraído, próximo, como se fossem amigos",
        "formal": "tom profissional e respeitoso",
        "artistico": "tom de artista apaixonado pelo trabalho, com personalidade forte",
    }.get(tone, "tom natural e autentico")

    return (
        f"Voce e um tatuador com nome artistico '{artist_name or 'o artista'}' "
        f"que trabalha com {tattoo_style or 'tatuagem'}"
        f"{' em ' + artist_city if artist_city else ''}.\n\n"
        f"Crie um template de mensagem para o seguinte cenario:\n{scenario}\n\n"
        f"Tom: {tone_desc}\n"
        f"Idioma: Portugues brasileiro\n"
        f"Use {'{nome}'} onde deve aparecer o nome do cliente.\n"
        f"O template deve ser autentico, nao parecer automatico ou robotico.\n"
        f"Maximo 150 palavras.\n\n"
        f"Retorne APENAS o texto do template, sem explicacoes ou titulos."
    )


# ─── Display ──────────────────────────────────────────────────────────────────


def _display_template(name: str, tmpl: dict) -> None:
    """Exibe template formatado."""
    from rich.panel import Panel
    from rich.text import Text

    console = display.console
    category = tmpl.get("category", "")
    channel = tmpl.get("channel", "")
    subject = tmpl.get("subject", name)
    text = tmpl.get("template", "")

    console.print()
    console.print(Panel(
        text,
        title=f"[bold red]{subject}[/bold red]  [dim]({category} — {channel})[/dim]",
        border_style="red",
    ))


def _display_all_templates(templates: dict) -> None:
    """Lista todos os templates (embutidos + customizados)."""
    from rich.table import Table
    from rich.panel import Panel

    console = display.console
    all_t: dict[str, dict] = {**BUILTIN_TEMPLATES, **templates}

    if not all_t:
        display.show_warning("Nenhum template disponivel.")
        return

    console.print()
    table = display.create_table(
        "Templates de Atendimento",
        [("ID", "yellow"), ("Categoria", "cyan"), ("Canal", "dim"), ("Assunto", "white")],
    )
    for i, (key, tmpl) in enumerate(all_t.items(), 1):
        table.add_row(
            str(i),
            tmpl.get("category", ""),
            tmpl.get("channel", ""),
            tmpl.get("subject", key),
        )
    console.print(table)
    return all_t


# ─── Fluxo principal ─────────────────────────────────────────────────────────


async def run_dm_templates(settings: dict) -> None:
    """Menu principal do modulo de templates de atendimento."""
    tattoo_style = settings.get("tattoo_style", "blackwork")
    artist_name = settings.get("artist_name", "")
    artist_city = settings.get("artist_city", "")

    custom_templates = storage.load_dm_templates()

    while True:
        display.console.print()
        display.show_panel(
            "Templates de Atendimento",
            "Mensagens prontas para DM e WhatsApp — personalize e copie!",
            style="cyan",
        )

        display.console.print()
        display.console.print("  [yellow]1[/yellow]  Ver todos os templates")
        display.console.print("  [yellow]2[/yellow]  Ver template especifico")
        display.console.print("  [yellow]3[/yellow]  Gerar template customizado com IA")
        display.console.print("  [yellow]4[/yellow]  Salvar template customizado")
        display.console.print("  [yellow]0[/yellow]  Voltar")
        display.console.print()

        choice = display.console.input("[bold cyan]Escolha > [/bold cyan]").strip()

        if choice == "0":
            break

        elif choice == "1":
            all_t = {**BUILTIN_TEMPLATES, **custom_templates}
            _display_all_templates(custom_templates)
            display.console.print()
            display.console.print(
                f"[dim]Total: {len(all_t)} templates ({len(BUILTIN_TEMPLATES)} embutidos + "
                f"{len(custom_templates)} customizados)[/dim]"
            )

        elif choice == "2":
            all_t = {**BUILTIN_TEMPLATES, **custom_templates}
            keys = list(all_t.keys())
            _display_all_templates(custom_templates)
            display.console.print()
            idx_str = display.console.input("[bold cyan]Numero do template > [/bold cyan]").strip()
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(keys):
                    key = keys[idx]
                    _display_template(key, all_t[key])
                    display.console.print()
                    display.show_tip(
                        "Copie o template, substitua os campos entre {chaves} e personalize antes de enviar!"
                    )
                else:
                    display.show_error("Numero invalido.")
            except ValueError:
                display.show_error("Numero invalido.")

        elif choice == "3":
            display.console.print()
            display.console.print("[bold]Descreva o cenario para o template:[/bold]")
            display.console.print("[dim]Ex: cliente perguntou se faço tatuagem colorida mas eu sou blackwork[/dim]")
            display.console.print()
            scenario = display.console.input("[bold cyan]Cenario > [/bold cyan]").strip()
            if not scenario:
                display.show_warning("Cenario vazio.")
                continue

            display.console.print()
            display.console.print("[bold]Tom da mensagem:[/bold]")
            display.console.print("  [yellow]1[/yellow]  Informal / descontraido")
            display.console.print("  [yellow]2[/yellow]  Formal / profissional")
            display.console.print("  [yellow]3[/yellow]  Artistico / personalidade forte")
            display.console.print()
            tone_choice = display.console.input("[bold cyan]Tom (1-3) > [/bold cyan]").strip()
            tone_map = {"1": "informal", "2": "formal", "3": "artistico"}
            tone = tone_map.get(tone_choice, "informal")

            prompt = _build_custom_template_prompt(
                scenario, tone, tattoo_style, artist_name, artist_city
            )
            display.console.print("[dim]Gerando template com IA...[/dim]")
            response = await ai_client.generate(prompt, settings, temperature=0.8)

            if response:
                display.console.print()
                from rich.panel import Panel
                display.console.print(Panel(
                    response,
                    title="[bold yellow]TEMPLATE GERADO[/bold yellow]",
                    border_style="yellow",
                ))
                display.console.print()
                save = display.console.input(
                    "[bold cyan]Salvar este template? (s/N) > [/bold cyan]"
                ).strip().lower()
                if save == "s":
                    tmpl_name = display.ask_input("Nome para o template (sem espacos)")
                    if tmpl_name:
                        key = re.sub(r"\W+", "_", tmpl_name.lower())
                        custom_templates[key] = {
                            "category": "Customizado",
                            "channel": "DM / WhatsApp",
                            "subject": tmpl_name,
                            "template": response,
                            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        }
                        storage.save_dm_templates(custom_templates)
                        display.show_success(f"Template '{tmpl_name}' salvo!")
            else:
                display.show_error("Nao foi possivel gerar o template.")

        elif choice == "4":
            display.console.print()
            display.console.print("[bold]Cole o texto do template:[/bold]")
            display.console.print("[dim](Pressione Enter duas vezes para finalizar)[/dim]")
            display.console.print()
            lines = []
            while True:
                line = display.console.input("").rstrip("\n")
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            template_text = "\n".join(lines).strip()

            if not template_text:
                display.show_warning("Template vazio.")
                continue

            tmpl_name = display.ask_input("Nome para o template")
            category = display.ask_input("Categoria (ex: Orcamento, Agendamento)", default="Geral")
            channel = display.ask_input("Canal (ex: DM, WhatsApp, Ambos)", default="DM / WhatsApp")

            if tmpl_name:
                key = re.sub(r"\W+", "_", tmpl_name.lower())
                custom_templates[key] = {
                    "category": category,
                    "channel": channel,
                    "subject": tmpl_name,
                    "template": template_text,
                    "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                storage.save_dm_templates(custom_templates)
                display.show_success(f"Template '{tmpl_name}' salvo!")
