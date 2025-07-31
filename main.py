import flet as ft
import time
import math
import base64
import requests
import httpx
from flet.core.types import MainAxisAlignment
from calculator import HP12C
from calculator import CalculatorInfix
import asyncio
import socket
import smtplib
import os
from email.message import EmailMessage

img = ft.Image(
    src="Icon.png",
    width=80,
    height=80,
    fit=ft.ImageFit.CONTAIN,
    border_radius=20,
    visible=False,
)
img_m = ft.Image(
    src="Icon.png",
    width=150,
    height=150,
    fit=ft.ImageFit.CONTAIN,
    border_radius=20,
)
class MyApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._main = None
        self.page.window.width = 450
        self.page.window.height = 700
        self.page.window.max_width = 450
        self.page.window.max_height = 700
        self.page.window.min_width = 450
        self.page.window.min_height = 700
        self.page.window.center()
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.vertical_alignment = "center"
        self.page.horizontal_alignment = "center"
        self.modo = {"valor": "normal"}
        self.page_atual = "inicial"
        self.modo2 = {"valor": "RPN"}
        self.calc = HP12C(self.update_display)
        self.infix = CalculatorInfix()
        self.display = ft.TextField(
        value="0", text_align=ft.TextAlign.RIGHT, read_only=True,
        bgcolor="#303030", color="white",
        border=ft.InputBorder.OUTLINE, height=80,
        text_style=ft.TextStyle(size=30),
        width=400, border_color="white", border_radius=10
        )
        self.bar = ft.ProgressBar(width=350, color="#000000", bgcolor="#eeeeee")
        self.page.bottom_appbar = ft.BottomAppBar(
            bgcolor="#303030",
            shape=ft.NotchShape.CIRCULAR,
            content=ft.Row(
                controls=[
                    ft.IconButton(icon=ft.Icons.SETTINGS, tooltip="Configurações", icon_color="white", icon_size=40, on_click= lambda e: self.sett(page)
                                  ),
                    ft.Container(expand=True),
                    img,
                    ft.Container(expand=True),
                    ft.Text("BETA", size=30, color="white"),
                ]
            )
        )

        self.txt_cal = ft.Text("Calculadoras", size=30, color="white")
        txt_ini = ft.Text("Iniciando...", size=12, color="white")
        self.txt = ft.Text("")
        self._main = ft.Container(
            width=400,
            height=550,
            bgcolor="#303030",
            border_radius=16,
            shadow=ft.BoxShadow(blur_radius=5, color="black"),
            content=ft.Column(
                [
                    ft.Row([self.txt_cal], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.txt], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.txt], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([img_m], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.txt], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.bar], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([txt_ini], alignment=ft.MainAxisAlignment.CENTER)
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        self._stack_main = ft.Stack(
            alignment=ft.alignment.center,
            controls=[self._main]
        )
        page.add(self._stack_main)
        self.iniciar_progresso(page)
        self._button = ft.Button(text="Bloco de notas", style=ft.ButtonStyle(text_style=ft.TextStyle(size=20)), bgcolor="white", color="#000f66", width=200, height=30)

    def iniciar_progresso(self, page):
        for i in range(101):
            self.bar.value = i / 100
            page.update()
            time.sleep(0.05)
        self.main_p(page)

    def sett(self, page):
        page.window.width = 450
        page.window.height = 700
        txt_sett = ft.Text("Configurações", size=30, color="white")
        txt_btt_tema = ft.Text(value="Tema #BREVE", color="white")
        btt_tema = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([txt_btt_tema], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=120, height=20, alignment=ft.alignment.center
            )
        )
        Back = ft.IconButton(icon=ft.Icons.ARROW_CIRCLE_LEFT, on_click=lambda e: self.back(page), tooltip="Voltar",
                             icon_color="white", icon_size=40)

        def suporte(e):
            self.page.launch_url("https://www.instagram.com/in_producoes_of/")
        txt_btt_spt = ft.Text(value="Suporte", color="white")
        btt_spt = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([txt_btt_spt], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=120, height=20, alignment=ft.alignment.center
            ), on_click= lambda e: suporte(e)
        )
        expan = ft.Container(expand=True)

        self._stack_main.controls.clear()
        self._stack_main.controls.append(
            ft.Container(
                width=400,
                height=550,
                bgcolor="#808080",
                border_radius=16,
                content=ft.Container(
                    width=400,
                    height=550,
                    bgcolor="#303030",
                    border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=5, color="black"),
                    content=ft.Column(
                        [
                            ft.Stack([ft.Row([expan, expan, expan, txt_sett, expan, Back],
                                             alignment=ft.MainAxisAlignment.CENTER)]),
                            ft.Row([btt_tema], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([btt_spt], alignment=ft.MainAxisAlignment.CENTER)
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    )
                )
            )
        )
        page.controls.clear()
        page.controls.append(self._stack_main)
        img.visible = True
        page.update()

    def rpn(self, page):

        def make_custom_button(label, color, bg, action_rpn, action_infix):
            tamanho = 20
            if color == "#":
                color = "white"
            if bg == "#":
                bg = "#303030"
            if label == "=":
                label = "ENTER"
                tamanho = 16

            def dynamic_action(e):
                if self.modo2["valor"] == "RPN":
                    action_rpn(e)
                else:
                    action_infix(e)

            text = ft.Text(value=label, color=color, size=tamanho)

            return ft.OutlinedButton(
                content=ft.Container(
                    content=ft.Column([text],
                                      alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                    width=60, height=60, alignment=ft.alignment.center, bgcolor=bg
                ),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                    bgcolor=ft.Colors.BLACK, padding=0
                ),
                on_click=dynamic_action
            )

        btn_modo_label = ft.Text("RPN", color="white", size=20)
        btn_enter_label = ft.Text("ENTER", color="white", size=16)

        def mudar_modo(e):
            if self.modo2["valor"] == "RPN":
                self.modo2["valor"] = "INFIX"
                btn_modo_label.value = "INFIX"
                btn_enter_label.value = "="
                btn_enter_label.size = 20
            else:
                self.modo2["valor"] = "RPN"
                btn_modo_label.value = "RPN"
                btn_enter_label.value = "ENTER"
                btn_enter_label.size = 16
            print(self.modo2)
            self.page.update()
            self.update_display()

        btn_enter = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([btn_enter_label],
                                  alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=60, height=60, alignment=ft.alignment.center, bgcolor="#b86b00"
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor=ft.Colors.BLACK, padding=0
            ),
            on_click=lambda e: self.on_enter_click()
        )

        btn_modo = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([btn_modo_label],
                                  alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=60, height=60, alignment=ft.alignment.center, bgcolor="#b86b00"
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor=ft.Colors.BLACK, padding=0
            ),
            on_click=lambda e: mudar_modo(e)
        )

        botoes1 = [
            make_custom_button("√x", "#b86b00", "#", lambda e: self.on_sqrt_click(), lambda e: self.infix_sqrt_click()),
            make_custom_button("Y^x", "#b86b00", "#", lambda e: self.on_square_click(), lambda e: self.infix_square_click()),
            make_custom_button("C", "#b86b00", "#", lambda e: self.on_c_click(), lambda e: self.infix_c_click()),
            make_custom_button("⇐", "#b86b00", "#", lambda e: self.handle_backspace_click(),lambda e: self.infix_backspace_click()),
            make_custom_button("%", "#b86b00", "#", lambda e: self.on_percent_click(), lambda e: self.infix_percent_click()),
            make_custom_button("÷", "#b86b00", "#", lambda e: self.on_divide_click(), lambda e: self.infix_divide_click())
        ]
        botoes2 = [
            make_custom_button("x!", "#b86b00", "#", lambda e: self.on_factorial_click(),lambda e: self.infix_factorial_click()),  # Buscar
            make_custom_button("lg", "#b86b00", "#", lambda e: self.on_lg_click(), lambda e: self.infix_lg_click()),  # Buscar
            make_custom_button("7", "#", "#", lambda e: self.on_digit_click("7")(e), lambda e: self.infix_digit_click("7")(e)),
            make_custom_button("8", "#", "#", lambda e: self.on_digit_click("8")(e), lambda e: self.infix_digit_click("8")(e)),
            make_custom_button("9", "#", "#", lambda e: self.on_digit_click("9")(e), lambda e: self.infix_digit_click("9")(e)),
            make_custom_button("×", "#b86b00", "#", lambda e: self.on_multiply_click(), lambda e: self.infix_multiply_click())
        ]
        botoes3 = [
            make_custom_button("1/x", "#b86b00", "#", lambda e: self.on_inverse_click(), lambda e: self.infix_inverse_click()),
            make_custom_button("ln", "#b86b00", "#", lambda e: self.on_ln_click(), lambda e: self.infix_ln_click()),  # Buscar
            make_custom_button("4", "#", "#", lambda e: self.on_digit_click("4")(e), lambda e: self.infix_digit_click("4")(e)),
            make_custom_button("5", "#", "#", lambda e: self.on_digit_click("5")(e), lambda e: self.infix_digit_click("5")(e)),
            make_custom_button("6", "#", "#", lambda e: self.on_digit_click("6")(e), lambda e: self.infix_digit_click("6")(e)),
            make_custom_button("-", "#b86b00", "#", lambda e: self.on_subtract_click(), lambda e: self.infix_subtract_click())
        ]
        botoes4 = [
            make_custom_button("π", "#b86b00", "#", lambda e: self.handle_pi_click(), lambda e: self.infix_pi_click()),
            make_custom_button("(", "#b86b00", "#", lambda e: print("Desativado"), lambda e: self.infix_digit_click("(")(e)),# Desativar no modo RPN
            make_custom_button("1", "#", "#", lambda e: self.on_digit_click("1")(e), lambda e: self.infix_digit_click("1")(e)),
            make_custom_button("2", "#", "#", lambda e: self.on_digit_click("2")(e), lambda e: self.infix_digit_click("2")(e)),
            make_custom_button("3", "#", "#", lambda e: self.on_digit_click("3")(e), lambda e: self.infix_digit_click("3")(e)),
            make_custom_button("+", "#b86b00", "#", lambda e: self.on_add_click(), lambda e: self.infix_add_click())
        ]
        botoes5 = [
            btn_modo,
            make_custom_button(")", "#b86b00", "#", lambda e: print("Desativado"), lambda e: self.infix_digit_click(")")(e)),# Desativar no modo RPN
            make_custom_button("e", "#", "#", lambda e: self.handle_e_click(), lambda e: self.infix_e_click()),  # Buscar
            make_custom_button("0", "#", "#", lambda e: self.on_digit_click("0")(e), lambda e: self.infix_digit_click("0")(e)),
            make_custom_button(",", "#", "#", lambda e: self.handle_dot_click(), lambda e: self.infix_dot_click()),
            btn_enter,
        ]
        row_botoes1 = ft.Row(botoes1, spacing=11, alignment=ft.MainAxisAlignment.START)
        row_botoes2 = ft.Row(botoes2, spacing=11, alignment=ft.MainAxisAlignment.START)
        row_botoes3 = ft.Row(botoes3, spacing=11, alignment=ft.MainAxisAlignment.START)
        row_botoes4 = ft.Row(botoes4, spacing=11, alignment=ft.MainAxisAlignment.START)
        row_botoes5 = ft.Row(botoes5, spacing=11, alignment=ft.MainAxisAlignment.START)

        Back = ft.IconButton(icon=ft.Icons.ARROW_CIRCLE_LEFT, tooltip="Voltar",icon_color="#303030", icon_size=40, on_click=lambda e: self.back(page))

        txt_IN_P = ft.Text("In Produções", size=20)

        txt_IN_P_Con = ft.Container(
            width=150,
            height=40,
            bgcolor="#303030",
            border_radius=16,
            shadow=ft.BoxShadow(blur_radius=5, color="black"),
            content=ft.Row([txt_IN_P], alignment=ft.MainAxisAlignment.CENTER)
        )
        self._stack_main.controls.clear()
        self._stack_main.controls.append(ft.Column([
            ft.Stack([
                ft.Container(
                    ft.Row([
                        ft.Container(expand=True), txt_IN_P_Con, ft.Container(expand=True), Back
                    ])
                )
            ]),
            ft.Stack([
               self.display
            ]),
            ft.Stack([
                ft.Column([
                    ft.Row([ft.Container(expand=True),row_botoes1,ft.Container(expand=True),]),
                    ft.Row([ft.Container(expand=True),row_botoes2,ft.Container(expand=True),]),
                    ft.Row([ft.Container(expand=True),row_botoes3,ft.Container(expand=True),]),
                    ft.Row([ft.Container(expand=True),row_botoes4],ft.Container(expand=True),),
                    ft.Row([ft.Container(expand=True),row_botoes5,ft.Container(expand=True),])
                ])
            ])
        ])
        )
        self.page.controls.clear()
        self.page.controls.append(self._stack_main)
        img.visible = True
        self.page.update()

    def hp(self, page):
        self.page.window.visible = False
        self.page.update()
        self.page.window.width = 700
        self.page.window.max_width = 700
        self.page.window.height = 450
        self.page.window.max_height = 450
        self.page.window.min_width = 700
        self.page.window.min_height = 450
        self.page.update()
        self.page.window.center()
        self.page.window.visible = True
        self.page.update()
        Back = ft.IconButton(icon=ft.Icons.ARROW_CIRCLE_LEFT, on_click=lambda e: self.back(page), tooltip="Voltar",
                             icon_color="#303030", icon_size=40, top=1, left=600)

        def make_custom_button(label, text_f, text_g, bg, fn_normal, fn_f, fn_g):
            top_text = ft.Text(value=text_f, size=8, color="#cc5729")
            center_text = ft.Text(value=label, color="white")
            bottom_text = ft.Text(value=text_g, size=10, color="#295fcc")

            def handle_click(e):
                match self.modo["valor"]:
                    case "normal":
                        fn_normal(e)
                    case "f":
                        fn_f(e)
                    case "g":
                        fn_g(e)

            return ft.OutlinedButton(
                content=ft.Container(
                    content=ft.Column([top_text, center_text, bottom_text],
                                      alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                    width=50, height=50, bgcolor=bg, alignment=ft.alignment.center
                ),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=0),
                    bgcolor=ft.Colors.BLACK, padding=0
                ),
                on_click=handle_click
            )

        # Função para mudar o modo atual
        def set_mode(new_mode):
            self.modo["valor"] = new_mode
            print(self.modo)
            self.page.update()

        # BOTOES POR FILEIRA
        botoes1 = [
            make_custom_button("n", "AMORT", "12x", "#303030", lambda e: self.handle_n_click(),
                               lambda e: self.handle_AMORT_click(), lambda e: self.handle_12x_click()),
            make_custom_button("i", "INT", "12÷", "#303030", lambda e: self.handle_i_click(), lambda e: self.handle_INT_click(),
                               lambda e: self.handle_12div_click()),
            make_custom_button("PV", "NPV", "CF0", "#303030", lambda e: self.handle_pv_click(),
                               lambda e: self.handle_npv_click(), lambda e: self.handle_CF0_click()),
            make_custom_button("PMT", "RND", "CFj", "#303030", lambda e: self.handle_pmt_click(),
                               lambda e: self.handle_RND_click(), lambda e: self.handle_CFj_click()),
            make_custom_button("FV", "IRR", "Nj", "#303030", lambda e: self.handle_fv_click(),
                               lambda e: self.handle_irr_click(), lambda e: self.handle_nj_click()),
            make_custom_button("CHS", "", "DATE", "#303030", lambda e: self.on_chs_click(), lambda e: print(""),
                               lambda e: print("g-n")),
            make_custom_button("7", "", "BEG", "#303030", lambda e: self.on_digit_click("7")(e), lambda e: self.precision("7"),
                               lambda e: self.handle_beg_click()),
            make_custom_button("8", "", "END", "#303030", lambda e: self.on_digit_click("8")(e), lambda e: self.precision("8"),
                               lambda e: print("g-n")),
            make_custom_button("9", "", "MEM", "#303030", lambda e: self.on_digit_click("9")(e), lambda e: self.precision("9"),
                               lambda e: print("g-n")),
            make_custom_button("÷", "", "", "#303030", lambda e: self.on_divide_click(), lambda e: print(""),
                               lambda e: print("")),

        ]
        botoes2 = [
            make_custom_button("Y^x", "PRICE", "√x", "#303030", lambda e: self.on_square_click(),
                               lambda e: self.handle_price_click(), lambda e: self.on_sqrt_click()),
            make_custom_button("1/x", "YTM", "e^x", "#303030", lambda e: self.on_inverse_click(),
                               lambda e: self.handle_ytm_click(), lambda e: self.handle_e_sob_x_click()),
            make_custom_button("%T", "SL", "LN", "#303030", lambda e: self.on_percent_total_click(),
                               lambda e: self.handle_sl_click(), lambda e: self.handle_ln_click()),
            make_custom_button("Δ%", "SOYD", "FRAC", "#303030", lambda e: self.on_delta_percent_click(),
                               lambda e: self.handle_soyd_click(), lambda e: self.handle_frac_click()),
            make_custom_button("%", "DB", "INTG", "#303030", lambda e: self.on_percent_click(),
                               lambda e: self.handle_db_click(), lambda e: self.handle_intg_click()),
            make_custom_button("EEX", "", "ΔDYS", "#303030", lambda e: self.handle_eex_click(), lambda e: print(""),
                               lambda e: self.handle_delta_dys_click()),
            make_custom_button("4", "", "D.MY", "#303030", lambda e: self.on_digit_click("4")(e), lambda e: self.precision("4"),
                               lambda e: self.handle_d_my_click()),
            make_custom_button("5", "", "D.DY", "#303030", lambda e: self.on_digit_click("5")(e), lambda e: self.precision("5"),
                               lambda e: self.handle_d_dy_click()),
            make_custom_button("6", "", "x̄ w", "#303030", lambda e: self.on_digit_click("6")(e), lambda e: self.precision("6"),
                               lambda e: self.handle_x_bar_w_click()),
            make_custom_button("×", "", "", "#303030", lambda e: self.on_multiply_click(), lambda e: print(""),
                               lambda e: print("")),
        ]
        botoes3 = [
            make_custom_button("R/S", "P/R", "PSE", "#303030", lambda e: self.handle_RS_click(),
                               lambda e: self.handle_PR_click(), lambda e: self.handle_pse_click()),
            make_custom_button("SST", "Σ", "BST", "#303030", lambda e: self.handle_SST_click(),
                               lambda e: self.handle_sigma_click(), lambda e: print("g-i")),
            make_custom_button("R▽", "PRGM", "GTO", "#303030", lambda e: self.on_roll_down_click(),
                               lambda e: self.handle_RS_click(), lambda e: self.handle_gto_click()),
            make_custom_button("X≷Y", "FIN", "x≤y", "#303030", lambda e: self.on_swap_click(),
                               lambda e: self.handle_fin_click(), lambda e: print("g-PMT")),
            make_custom_button("CLx", "REG", "x=0", "#303030", lambda e: self.on_clx_click(), lambda e: self.handle_reg_click(),
                               lambda e: print("g-FV")),
            make_custom_button("", "", "", "#303030", lambda e: print(""), lambda e: print(""), lambda e: print("g-n")),
            make_custom_button("1", "", "x̂, r", "#303030", lambda e: self.on_digit_click("1")(e), lambda e: self.precision("1"),
                               lambda e: print("g-n")),
            make_custom_button("2", "", "ŷ, r", "#303030", lambda e: self.on_digit_click("2")(e), lambda e: self.precision("2"),
                               lambda e: print("g-n")),
            make_custom_button("3", "", "n!", "#303030", lambda e: self.on_digit_click("3")(e), lambda e: self.precision("3"),
                               lambda e: self.handle_fatorial_click()),
            make_custom_button("-", "", "⇐", "#303030", lambda e: self.on_subtract_click(), lambda e: print(""),
                               lambda e: self.handle_backspace_click()),

        ]
        botoes4 = [
            make_custom_button("ON", "", "", "#303030", lambda e: self.on_ON_click(), lambda e: print(""),
                               lambda e: print("")),
            make_custom_button("f", "", "", "#b86b00", lambda e: set_mode("f"), lambda e: set_mode("f"),
                               lambda e: set_mode("f")),
            make_custom_button("g", "", "", "#0087b8", lambda e: set_mode("g"), lambda e: set_mode("g"),
                               lambda e: set_mode("g")),
            make_custom_button("STO", "", "", "#303030", lambda e: self.handle_sto_click(), lambda e: print(""),
                               lambda e: print("")),
            make_custom_button("RCL", "", "", "#303030", lambda e: self.handle_rcl_click(), lambda e: print(""),
                               lambda e: print("")),
            make_custom_button("", "", "", "#303030", lambda e: print("n"), lambda e: print(""), lambda e: print("")),
            make_custom_button("0", "", "x̄", "#303030", lambda e: self.on_digit_click("0")(e), lambda e: self.precision("0"),
                               lambda e: self.handle_x_bar_click()),
            make_custom_button(".", "", "s", "#303030", lambda e: self.handle_dot_click(), lambda e: print(""),
                               lambda e: self.handle_desvio_padrao_click()),
            make_custom_button("Σ+", "", "Σ-", "#303030", lambda e: self.sigma_plus_action(), lambda e: print(""),
                               lambda e: self.sigma_minus_action()),
            make_custom_button("+", "", "", "#303030", lambda e: self.on_add_click(), lambda e: print(""),
                               lambda e: print("")),

        ]

        row_botoes1 = ft.Row(botoes1, spacing=5, alignment=ft.MainAxisAlignment.START)
        row_botoes2 = ft.Row(botoes2, spacing=5, alignment=ft.MainAxisAlignment.START)
        row_botoes3 = ft.Row(botoes3, spacing=5, alignment=ft.MainAxisAlignment.START)
        row_botoes4 = ft.Row(botoes4, spacing=5, alignment=ft.MainAxisAlignment.START)

        # ENTER
        enter_btn = ft.Container(
            content=(
                ft.Column([
                    ft.Row([ft.Text("PREFIX", color="orange", size=8)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("E", color="white", size=11)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("N", color="white", size=11)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("T", color="white", size=11)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("E", color="white", size=11)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("R", color="white", size=11)], alignment=MainAxisAlignment.CENTER),
                    ft.Row([ft.Text("LSTx", color="cyan", size=8)], alignment=MainAxisAlignment.CENTER)
                ], spacing=0)
            ),

            width=56, height=110, bgcolor="#303030",
            alignment=ft.alignment.center, left=305, top=120,
            on_click=lambda e: self.on_enter_click_hp(),
            border=ft.border.all(1, "gray")
        )

        self._stack_main.controls.clear()
        self._stack_main.controls.append(ft.Column([
            ft.Stack([
                ft.Row([self.display,ft.Container(expand=True), img, ft.Container(expand=True)]),
                Back,
            ]),
            ft.Stack([
                ft.Column([
                    row_botoes1,
                    row_botoes2,
                    row_botoes3,
                    row_botoes4,
                ]),
                enter_btn,
            ])
        ])
        )
        self.page.controls.clear()
        self.page.controls.append(self._stack_main)
        img.visible = True
        self.page.update()

    def back(self, page):
        self.main_p(page)
        self.page.update()

    def main_p(self, page: ft.Page):
        self.page.window.visible = False
        self.page.update()
        self.page.window.width = 450
        self.page.window.max_width = 450
        self.page.window.min_width = 450
        self.page.window.height = 700
        self.page.window.max_height = 700
        self.page.window.min_height = 700
        self.page.update()
        self.page.window.center()
        self.page.window.visible = True
        self.page.update()


        # BTT RPN
        txt_btt_cal = ft.Text(value="Calculadora RPN", color="white")
        btt_cal_rpn = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([txt_btt_cal], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=120, height=20, alignment=ft.alignment.center
            ),on_click= self.rpn

        )

        # BTT HP
        txt_btt_hp = ft.Text(value="HP-12C", color="white")
        btt_hp = ft.OutlinedButton(
            content=ft.Container(
                content=ft.Column([txt_btt_hp], alignment=ft.MainAxisAlignment.CENTER, spacing=1),
                width=120, height=20, alignment=ft.alignment.center
            ), on_click=self.hp
        )
        self._stack_main.controls.clear()
        self._stack_main.controls.append(ft.Container(
                width=400,
                height=550,
                bgcolor="#808080",
                border_radius=16,
                content=ft.Container(
                    width=400,
                    height=550,
                    bgcolor="#303030",
                    border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=5, color="black"),
                    content=ft.Column(
                        [
                            ft.Row([self.txt_cal], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([btt_cal_rpn], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row([btt_hp], alignment=ft.MainAxisAlignment.CENTER)
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    )
                )
            )
        )

        self.page.controls.clear()
        self.page.controls.append(self._stack_main)
        img.visible = True
        self.page.update()

    def update_display(self):
        self.display.value = self.calc.get_display()
        self.page.update()

    def on_digit_click(self, digit):
        def handler(e):
            self.calc.push_number(digit)
        return handler

    def on_ON_click(self):
        self.display.value = self.calc.get_display()
        self.calc.toggle_decimal_display()

    def handle_LsTx_click(self):
        self.calc.lstx()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def on_enter_click_hp(self):
        self.calc.enter()

    def on_enter_click(self):
        match self.modo2["valor"]:
            case "RPN":
                self.calc.enter()
            case "INFIX":
                self.infix.press("=")
                self.display.value = self.infix.input
                self.page.update()

    def on_add_click(self):
        self.calc.add()

    def on_subtract_click(self):
        self.calc.subtract()

    def on_multiply_click(self):
        self.calc.multiply()

    def on_divide_click(self):
        self.calc.divide()

    def on_chs_click(self):
        self.calc.chs()

    def on_clx_click(self):
        self.calc.clx()

    def on_roll_down_click(self):
        self.calc.stack = [self.calc.X, self.calc.T, self.calc.Z, self.calc.Y]
        self.update_display()

    def on_swap_click(self):
        self.calc.stack[2], self.calc.stack[3] = self.calc.stack[3], self.calc.stack[2]
        self.update_display()

    def precision(self, digit):
        self.calc.precision = int(digit)
        self.calc.update_display()
        self.update_display()
        self.modo["valor"] = "normal"
        print(self.modo)

    def on_sqrt_click(self):
        if self.calc.X >= 0:
            self.calc.X = math.sqrt(self.calc.X)
        else:
            self.calc.X = float("nan")
        self.update_display()
        self.modo["valor"] = "normal"
        print(self.modo)

    def on_inverse_click(self):
        if self.calc.X != 0:
            self.calc.X = 1 / self.calc.X
        else:
            self.calc.X = float("inf")
        self.update_display()

    def on_square_click(self):
        self.calc.X = self.calc.Y ** self.calc.X
        self.update_display()

    def on_percent_click(self):
        self.calc.X = self.calc.Y * (self.calc.X / 100)
        self.update_display()

    def on_percent_total_click(self):
        self.calc.percent_total()
        self.update_display()

    def on_delta_percent_click(self):
        self.calc.delta_percent()
        self.update_display()

    def handle_n_click(self):
        self.calc.store_financial_value("n", self.calc.X)
        if self.calc.vars["n"] == 0:
            self.calc.calculate_n()

    def handle_pv_click(self):
        self.calc.store_financial_value("PV", self.calc.X)
        if self.calc.vars["PV"] == 0:
            self.calc.calculate_pv()

    def handle_pmt_click(self):
        self.calc.store_financial_value("PMT", self.calc.X)
        if self.calc.vars["PMT"] == 0:
            self.calc.calculate_pmt()

    def handle_fv_click(self):
        self.calc.store_financial_value("FV", self.calc.X)
        if self.calc.vars["FV"] == 0:
            self.calc.calculate_fv()

    def handle_i_click(self):
        self.calc.store_financial_value("i", self.calc.X)
        if self.calc.vars["i"] == 0:
            self.calc.calculate_i()

    def handle_sto_click(self):
        self.calc.sto()

    def handle_rcl_click(self):
        self.calc.rcl()

    def handle_dot_click(self):
        self.calc.input_dot()

    def sigma_plus_action(self):
        try:
            self.calc.sigma_plus()
            self.update_display()
        except Exception as e:
            print("Erro no Sigma+: ", e)

    def sigma_minus_action(self):
        self.calc.sigma_minus()
        self.update_display()
        self.modo["valor"] = "normal"
        print(self.modo)
        self.page.update()

    def handle_backspace_click(self):
        self.calc.backspace()
        self.update_display()
        self.modo["valor"] = "normal"
        print(self.modo)
        self.page.update()

    def handle_eex_click(self):
        self.calc.eex()
        self.update_display()

    def handle_PR_click(self):
        self.calc.toggle_program_mode()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_RS_click(self):
        self.calc.run_stop()
        self.update_display()

    def handle_SST_click(self):
        self.calc.sst()
        self.update_display()

    def handle_AMORT_click(self):
        self.calc.amort()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_INT_click(self):
        self.calc.int_juros()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_CF0_click(self):
        self.calc.cf0()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_CFj_click(self):
        self.calc.cfj()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_nj_click(self):
        self.calc.nj()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_npv_click(self):
        self.calc.npv()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_RND_click(self):
        self.calc.rnd()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_irr_click(self):
        self.calc.irr()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_price_click(self):
        self.calc.price()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_ytm_click(self):
        self.calc.ytm()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_sl_click(self):
        self.calc.sl()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_soyd_click(self):
        self.calc.soyd()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_db_click(self):
        self.calc.db()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_sigma_click(self):
        self.calc.sigma_normal()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_fin_click(self):
        self.calc.fin()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_reg_click(self):
        self.calc.reg()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_12x_click(self):
        self.calc.twelve_x()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_12div_click(self):
        self.calc.twelve_divide()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_beg_click(self):
        self.calc.begin()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_e_sob_x_click(self):
        self.calc.e_x()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_ln_click(self):
        self.calc.ln()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_frac_click(self):
        self.calc.frac()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_intg_click(self):
        self.calc.intg()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_delta_dys_click(self):
        self.calc.delta_dys()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_d_my_click(self):
        self.calc.d_my()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_d_dy_click(self):
        self.calc.d_dy()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_x_bar_w_click(self):
        self.calc.x_bar_w()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_pse_click(self):
        self.calc.pse()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_fatorial_click(self):
        self.calc.fatorial()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_gto_click(self):
        self.calc.gto_from_stack()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_desvio_padrao_click(self):
        self.calc.desvio_padrao()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def handle_x_bar_click(self):
        self.calc.x_bar()
        self.update_display()
        self.modo["valor"] = "normal"
        self.page.update()

    def on_c_click(self):
        self.calc.c()

    #DEF INFIX
    def handle_pi_click(self):
        self.calc.X = 3.14

    def on_factorial_click(self):
        self.calc.X = math.factorial(int(self.calc.X))
        self.update_display()

    def on_lg_click(self):
        self.calc.X = math.log10(self.calc.X)
        self.update_display()

    def on_ln_click(self):
        self.calc.X = math.log(self.calc.X)
        self.update_display()

    def handle_e_click(self):
        self.calc.X = math.e
        self.update_display()

    def infix_digit_click(self, d):
        def handler(e):
            self.infix.input += d
            self.display.value = self.infix.input
            self.page.update()

        return handler

    def infix_add_click(self):
        self.infix.press("+")
        self.display.value = self.infix.input

    def infix_subtract_click(self):
        self.infix.press("-")
        self.display.value = self.infix.input

    def infix_multiply_click(self):
        self.infix.press("×")
        self.display.value = self.infix.input

    def infix_divide_click(self):
        self.infix.press("÷")
        self.display.value = self.infix.input

    def infix_c_click(self):
        self.infix.press("C")
        self.display.value = self.infix.input

    def infix_backspace_click(self):
        self.infix.press("⇐")
        self.display.value = self.infix.input
        self.on_enter_click()

    def infix_percent_click(self):
        self.infix.press("%")
        self.display.value = self.infix.input
        self.on_enter_click()

    def infix_sqrt_click(self):
        self.infix.press("√x")
        self.display.value = self.infix.input
        self.on_enter_click()

    def infix_square_click(self):
        self.infix.press("Y^x")
        self.display.value = self.infix.input

    def infix_factorial_click(self):
        self.infix.press("x!")
        self.display.value = self.infix.input

    def infix_lg_click(self):
        self.infix.press("lg")
        self.display.value = self.infix.input

    def infix_ln_click(self):
        self.infix.press("ln")
        self.display.value = self.infix.input

    def infix_inverse_click(self):
        self.infix.press("1/x")
        self.display.value = self.infix.input

    def infix_pi_click(self):
        self.infix.press("π")
        self.display.value = self.infix.input

    def infix_e_click(self):
        self.infix.press("e")
        self.display.value = self.infix.input

    def infix_dot_click(self):
        self.infix.press(",")
        self.display.value = self.infix.input

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=MyApp, view=ft.AppView.WEB_BROWSER, port=port)
