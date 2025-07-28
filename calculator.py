import math
import time

class CalculatorInfix:
    def __init__(self):
        self.input = ""
        self.result = ""

    def press(self, char):
        if char in "0123456789":
            self.input += char
        elif char == ",":
            self.input += "."  # vírgula vira ponto
        elif char in "+-*/":
            self.input += f" {char} "
        elif char == "×":
            self.input += " * "
        elif char == "÷":
            self.input += " / "
        elif char == "π":
            self.input += str(math.pi)
        elif char == "e":
            self.input += str(math.e)
        elif char == "(" or char == ")":
            self.input += char
        elif char == "√x":
            self._wrap_last_number("math.sqrt")
        elif char == "Y^x":
            self.input += " ** "
        elif char == "%":
            self._wrap_last_number("/100")
        elif char == "x!":
            self._wrap_last_number("math.factorial")
        elif char == "lg":
            self._wrap_last_number("math.log10")
        elif char == "ln":
            self._wrap_last_number("math.log")
        elif char == "1/x":
            self._wrap_last_number("1/(")
        elif char == "⇐":
            self.input = self.input[:-1]
        elif char == "C":
            self.input = ""
        elif char == "=":
            self.result = self.evaluate()
            self.input = self.result

    def _last_number(self):
        return self.input.strip().split(" ")[-1]

    def _replace_last_number(self, new_value):
        parts = self.input.strip().split(" ")
        parts[-1] = new_value
        self.input = " ".join(parts)

    def _wrap_last_number(self, func, suffix=")"):
        try:
            n = self._last_number()
            self._replace_last_number(f"{func}({n}{suffix}")
        except:
            self.input = "ERROR"

    def evaluate(self):
        try:
            return str(eval(self.input, {"math": math, "__builtins__": {}}, {}))
        except:
            return "ERROR"

class HP12C:

    def __init__(self, update_display):
        self.update_display = update_display
        self.stack = [0.0, 0.0, 0.0, 0.0]  # [T, Z, Y, X]
        self.input_buffer = ""
        self.stack_locked = False
        self.vars = {"n": 0, "i": 0, "PV": 0, "PMT": 0, "FV": 0}
        self.memory = {str(i): 0.0 for i in range(10)}  # memória de 10 registradores: "0" a "9"
        self.waiting_for_sto_register = False
        self.waiting_for_rcl_register = False
        self.sigma = {'n': 0,'Σx': 0.0,'Σx²': 0.0,'Σy': 0.0,'Σy²': 0.0,'Σxy': 0.0}
        self.sigma_stack = []
        self.precision = 2  # Precisão padrão com 2 casas decimais
        self.use_comma = False
        self.modo_programa_ativo = False
        self.programa = []  # Lista de comandos
        self.program_counter = 0
        self.executando_programa = False
        self.fluxos_de_caixa = []  # Ex: [(CF0, 1), (CF1, 1), (CF2, 3)]
        self.ultimo_x = 0.0

    @property
    def X(self): return self.stack[3]
    @X.setter
    def X(self, value): self.stack[3] = value

    @property
    def Y(self): return self.stack[2]
    @Y.setter
    def Y(self, value): self.stack[2] = value

    @property
    def Z(self): return self.stack[1]
    @Z.setter
    def Z(self, value): self.stack[1] = value

    @property
    def T(self): return self.stack[0]
    @T.setter
    def T(self, value): self.stack[0] = value

    def desvio_padrao(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.desvio_padrao)
        else:
            try:
                n = self.sigma['n']
                if n <= 1:
                    self.X = 0.0
                else:
                    media = self.sigma['Σx'] / n
                    variancia = (self.sigma['Σx²'] - n * media ** 2) / (n - 1)
                    self.X = variancia ** 0.5
                self.update_display()
            except Exception as e:
                print("Erro no desvio padrão:", e)

    def x_bar(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.x_bar)
        else:
            try:
                if self.sigma['n'] == 0:
                    self.X = 0.0
                else:
                    self.X = self.sigma['Σx'] / self.sigma['n']
                self.update_display()
            except Exception as e:
                print("Erro no cálculo de x̄:", e)

    def lstx(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.lstx)
        else:
            self.push_number(self.ultimo_x)

    def gto(self, linha):
        if self.modo_programa_ativo:
            self.record_instruction(self.gto)
        """Vai diretamente para a linha especificada do programa"""
        if 0 <= linha < len(self.programa):
            self.program_counter = linha
            print(f"GTO: pulando para a linha {linha}")
        else:
            print(f"Erro: linha {linha} não existe no programa")

    def gto_from_stack(self):
        """Pega a linha de destino do topo da pilha (X) e vai até lá"""
        linha = int(self.X)
        self.gto(linha)

    def fatorial(self):
        if self.X < 0 or int(self.X) != self.X:
            print("Erro: fatorial só é definido para inteiros não negativos.")
            return
        self.X = math.factorial(int(self.X))
        print(f"n!: {self.X}")

    def bst(self):
        if self.modo_programa_ativo and self.programa:
            self.program_counter = max(0, self.program_counter - 1)
            print(f"BST: posição atual do programa = {self.program_counter}")

    def pse(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.pse)
        if not self.modo_programa_ativo:
            return  # Só funciona em modo de execução de programa

        time.sleep(1)  # Pausa de 1 segundo

    def x_bar_w(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.x_bar_w)
        try:
            soma_y = self.sigma["Σy"]
            if soma_y == 0:
                raise ZeroDivisionError("Divisão por zero: soma dos pesos Y é zero.")

            media_ponderada = self.sigma["Σxy"] / soma_y
            self.X = round(media_ponderada, 10)
            print(f"Média ponderada (x̄ w): {self.X}")
        except Exception as e:
            print("Erro no cálculo de x̄ w:", e)

    def delta_dys(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.delta_dys)
        try:
            def corrigir_data(data_float):
                data_str = str(data_float)
                if "." not in data_str:
                    raise ValueError("Data mal formatada")

                dia, resto = data_str.split(".")
                if len(dia) == 1:
                    dia = "0" + dia  # Adiciona zero à esquerda no dia

                mes = resto[:2]
                ano = resto[2:]
                return f"{dia}.{mes}{ano}"

            def dias_360(data1, data2):
                from datetime import datetime
                d1 = datetime.strptime(data1, "%d.%m%Y")
                d2 = datetime.strptime(data2, "%d.%m%Y")

                d1_dia = min(d1.day, 30)
                d2_dia = min(d2.day, 30)

                return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (d2_dia - d1_dia)

            data_inicial = corrigir_data(self.Y)
            data_final = corrigir_data(self.X)
            dias = dias_360(data_inicial, data_final)
            self.X = dias
            print(f"ΔDYS entre {data_inicial} e {data_final}: {dias} dias")
        except Exception as e:
            print("Erro no ΔDYS:", e)

    def d_my(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.d_my)
        try:
            # A entrada esperada é uma quantidade de dias (como vinda de ΔDYS)
            dias = self.X
            meses = dias / 30  # Base 30 dias por mês
            self.X = round(meses, 10)
            print(f"D.MY convertido: {dias} dias = {self.X} meses")
        except Exception as e:
            print("Erro no D.MY:", e)

    def d_dy(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.d_dy)
        try:
            meses = self.X
            dias = meses * 30
            self.X = round(dias, 10)
            print(f"D.DY convertido: {meses} meses = {self.X} dias")
        except Exception as e:
            print("Erro no D.DY:", e)

    def frac(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.frac)

        try:
            self.X = self.X - int(self.X)  # pega apenas a parte fracionária
            self.update_display()
            print(f"Parte fracionária: {self.X}")
        except Exception as e:
            print(f"Erro ao calcular parte fracionária: {e}")

    def intg(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.intg)

        # Realiza um cálculo de integral simples (somatório de uma função)
        try:
            self.X += self.Y  # Supondo que a integral seja a soma de X com Y (um exemplo simples)
            self.update_display()
            print(f"Resultado da integral: {self.X}")
        except Exception as e:
            print(f"Erro ao calcular a integral: {e}")

    def e_x(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.e_x)

        self.X = math.exp(self.X)  # Calcula e^X
        self.update_display()
        print(f"Calculando e^X: {self.X}")

    def ln(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.ln)

        if self.X > 0:
            self.X = math.log(self.X)  # Calcula o logaritmo natural de X
            self.update_display()
            print(f"Calculando LN(X): {self.X}")
        else:
            print("Erro: LN de número não positivo!")

    def twelve_x(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.twelve_x)

        self.X = self.X * 12  # Multiplica o valor de X por 12
        self.update_display()
        print(f"Multiplicando X por 12: {self.X}")

    def twelve_divide(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.twelve_divide)

        if self.X != 0:
            self.X = self.X / 12  # Divide o valor de X por 12
            self.update_display()
            print(f"Dividindo X por 12: {self.X}")
        else:
            print("Erro: Divisão por zero!")

    def begin(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.begin)

        self.vars["mode"] = "begin"  # Ativa o modo "begin"
        self.update_display()
        print("Modo 'Begin' ativado.")

    def fin(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.fin)

        for var in ["n", "i", "PV", "PMT", "FV"]:
            self.vars[var] = 0.0
        self.X = 0.0
        print("Variáveis financeiras limpas (n, i, PV, PMT, FV).")
        self.update_display()

    def reg(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.reg)

        # Limpa variáveis financeiras
        for var in ["n", "i", "PV", "PMT", "FV"]:
            self.vars[var] = 0.0

        # Limpa a pilha
        self.X = self.Y = self.Z = self.T = 0.0

        # Limpa memórias R0–R9
        self.memorias = {f"R{i}": 0.0 for i in range(10)}

        # Limpa estatísticas Σ
        self.sigma = {
            "n": 0,
            "Σx": 0.0,
            "Σy": 0.0,
            "Σx²": 0.0,
            "Σy²": 0.0,
            "Σxy": 0.0
        }
        self.sigma_stack = []

        print("Todos os registros e dados estatísticos foram limpos.")
        self.update_display()

    def db(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.db)

        PV = self.vars.get("PV", 0)
        n = self.vars.get("n", 1)

        if PV <= 0 or n <= 0:
            self.X = 0
            self.update_display()
            return

        taxa = 1 / n
        depreciacao = round(PV * taxa, 2)

        self.X = depreciacao
        print("DB - Depreciação do 1º ano:", self.X)
        self.update_display()

    def soyd(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.soyd)

        valor_inicial = self.vars.get("PV", 0)
        valor_residual = self.vars.get("FV", 0)
        vida_util = int(self.vars.get("n", 0))
        ano = int(self.vars.get("i", 1))  # ano desejado

        if vida_util == 0 or ano < 1 or ano > vida_util:
            self.X = 0.0
            return

        soma_dos_anos = vida_util * (vida_util + 1) // 2
        depreciacao = ((vida_util - (ano - 1)) / soma_dos_anos) * (valor_inicial - valor_residual)

        self.X = depreciacao
        self.update_display()

    def sl(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.sl)

        valor_inicial = self.vars.get("PV", 0)
        valor_residual = self.vars.get("FV", 0)
        vida_util = self.vars.get("n", 0)

        if vida_util == 0:
            self.X = 0.0
        else:
            depreciacao_anual = (valor_inicial - valor_residual) / vida_util
            self.X = depreciacao_anual

        self.update_display()

    def ytm(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.ytm)

        n = self.vars.get("n", 0)
        pmt = self.vars.get("PMT", 0)
        fv = self.vars.get("FV", 0)
        pv = self.vars.get("PV", 0)

        if n == 0 or pv == 0:
            self.X = 0.0
            self.update_display()
            return

        # Transformar PV em negativo, se não estiver
        pv = -abs(pv)

        # Chute inicial da taxa
        guess = 0.05
        tol = 1e-6
        max_iter = 100

        for _ in range(max_iter):
            denom = (1 + guess) ** n
            price = (pmt * (1 - 1 / denom) / guess) + fv / denom
            d_price = (-pmt * (1 - 1 / denom) / (guess ** 2)) + (pmt * n / (denom * (1 + guess))) - (
                        n * fv / (denom * (1 + guess)))

            error = price - (-pv)
            if abs(error) < tol:
                break
            guess -= error / d_price

        self.X = guess * 100  # Em percentual
        self.update_display()

    def price(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.price)

        n = self.vars.get("n", 0)
        i = self.vars.get("i", 0)
        pmt = self.vars.get("PMT", 0)
        fv = self.vars.get("FV", 0)

        if n == 0 or i == 0:
            self.X = 0.0
        else:
            rate = i / 100
            if rate == 0:
                price = pmt * n + fv
            else:
                price = (pmt * (1 - (1 + rate) ** -n) / rate) + fv / ((1 + rate) ** n)

            self.X = price

        self.update_display()

    def irr(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.irr)

        if not self.fluxos_de_caixa:
            self.X = 0.0
            self.update_display()
            return

        def npv(rate):
            total = 0
            for i, (valor, rep) in enumerate(self.fluxos_de_caixa):
                for r in range(rep):
                    total += valor / ((1 + rate) ** (i + r))
            return total

        # Metodo de Newton-Raphson para encontrar o IRR
        rate = 0.1  # chute inicial (10%)
        for _ in range(100):
            f = npv(rate)
            f_prime = (npv(rate + 1e-5) - f) / 1e-5
            if abs(f_prime) < 1e-10:
                break
            rate -= f / f_prime
            if abs(f) < 1e-6:
                break

        self.X = rate * 100  # Mostra como porcentagem
        self.update_display()

    def rnd(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.rnd)

        rounded_value = round(self.X, self.precision)
        print(f"Arredondando {self.X} para {self.precision} casas decimais: {rounded_value}")
        self.X = rounded_value
        self.update_display()

    def cf0(self):
        self.fluxos_de_caixa = [(self.X, 1)]

    def cfj(self):
        self.fluxos_de_caixa.append((self.X, 1))

    def nj(self):
        if self.fluxos_de_caixa:
            valor, _ = self.fluxos_de_caixa[-1]
            self.fluxos_de_caixa[-1] = (valor, int(self.X))

    def npv(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.npv)

        taxa = self.vars.get("i", 0) / 100
        fluxo_caixa = self.fluxos_de_caixa  # Lista de tuplas: (valor, repetições)

        npv_total = 0
        periodo = 1

        for valor, repeticoes in fluxo_caixa[1:]:  # Ignora CF0 no início
            for _ in range(repeticoes):
                npv_total += valor / ((1 + taxa) ** periodo)
                periodo += 1

        # Adiciona o fluxo inicial
        npv_total += fluxo_caixa[0][0]

        self.X = npv_total
        print(f"NPV calculado: {npv_total}")
        self.update_display()

    def amort(self, periods=1):
        if self.modo_programa_ativo:
            self.record_instruction(self.amort)

        # Obtem os dados financeiros
        i = self.vars.get("i", 0)
        saldo = self.vars.get("PV", 0)
        pmt = self.vars.get("PMT", 0)

        juros_total = 0
        amortizacao_total = 0

        for _ in range(periods):
            juros = saldo * (i / 100)
            amortizacao = abs(pmt) - juros
            saldo += amortizacao  # A dívida aumenta se amortização for negativa
            juros_total += juros
            amortizacao_total += amortizacao

        self.X = -juros_total  # O que aparece no display da HP-12C: juros negativos
        self.Y = -amortizacao_total  # Amortização negativa
        self.Z = saldo  # Novo saldo (pode aumentar ou diminuir)
        self.vars["PV"] = saldo  # Atualiza o PV armazenado

        print(f"Juros pagos: {-juros_total}")
        print(f"Amortização do principal: {-amortizacao_total}")
        print(f"Novo saldo (PV): {saldo}")
        self.update_display()

    def int_juros(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.int_juros)

        juros = self.vars.get("juros_ultimo_amort", 0)
        self.X = juros
        print(f"Reexibindo juros do último AMORT: {self.X}")
        self.update_display()

    def toggle_program_mode(self):
        self.modo_programa_ativo = not self.modo_programa_ativo
        print("Modo de programa:", "Ativo" if self.modo_programa_ativo else "Desativado")

    def record_instruction(self, func):
        if self.modo_programa_ativo:
            self.programa.append(func)
            print("Comando gravado. Total:", len(self.programa))

    def sst(self):
        if self.program_counter < len(self.programa):
            print(f"Executando passo {self.program_counter + 1}: {self.programa[self.program_counter].__name__}")
            self.programa[self.program_counter]()
            self.program_counter += 1
        else:
            print("Fim do programa.")
            self.program_counter = 0

    def run_stop(self):
        if self.executando_programa:
            self.executando_programa = False
            print("Execução interrompida.")
        else:
            self.executando_programa = True
            print("Execução iniciada...")
            while self.program_counter < len(self.programa) and self.executando_programa:
                self.sst()
            self.executando_programa = False
            self.program_counter = 0

    def delta_percent(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.delta_percent)
        if self.Y != 0:
            self.X = ((self.X - self.Y) / self.Y) * 100
        else:
            self.X = 0.0
        self.update_display()

    def percent_total(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.percent_total)
        if self.Y != 0:
            self.X = (self.X / self.Y) * 100
        else:
            self.X = 0.0
        self.update_display()

    def toggle_decimal_display(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.toggle_decimal_display)
        self.use_comma = not self.use_comma
        self.update_display()

    def eex(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.eex)
        if self.input_buffer:
            self.X = float(self.input_buffer)
            self.input_buffer = ''
        self.entering_exponent = True
        self.exponent_buffer = ''

    def input_dot(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.input_dot)
        if '.' not in self.input_buffer:
            if self.input_buffer == '':
                self.input_buffer = '0.'
            else:
                self.input_buffer += '.'
        self.update_display()

    def backspace(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.backspace)
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]
            self.X = float(self.input_buffer) if self.input_buffer else 0.0
            self.update_display()

    def sigma_normal(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.sigma)

        self.sigma["n"] += 1
        self.sigma["Σx"] += self.X
        self.sigma["Σy"] += self.Y
        self.sigma["Σx²"] += self.X ** 2
        self.sigma["Σy²"] += self.Y ** 2
        self.sigma["Σxy"] += self.X * self.Y

        print("Dados estatísticos atualizados:")
        print(self.sigma)

    def sigma_plus(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.sigma_plus)
        self.sigma["n"] += 1
        self.sigma["Σx"] += self.X
        self.sigma["Σx²"] += self.X ** 2
        self.sigma["Σy"] += self.Y
        self.sigma["Σy²"] += self.Y ** 2
        self.sigma["Σxy"] += self.X * self.Y
        self.sigma_stack.append((self.Y, self.X))  # Salva o par (Y, X)
        print(self.sigma)

    def sigma_minus(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.sigma_minus)
        if self.sigma_stack:
            y, x = self.sigma_stack.pop()
            self.sigma["n"] -= 1
            self.sigma["Σx"] -= x
            self.sigma["Σx²"] -= x ** 2
            self.sigma["Σy"] -= y
            self.sigma["Σy²"] -= y ** 2
            self.sigma["Σxy"] -= x * y
            print(self.sigma)
        else:
            print("Nada para remover")

    def sto(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.sto)
        self.waiting_for_sto_register = True
        print("STO ativado — aguardando número do registrador...")

    def rcl(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.rcl)
        self.waiting_for_rcl_register = True
        print("RCL ativado — aguardando número do registrador...")

    def enter(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.enter)
        if self.input_buffer:
            self.X = float(self.input_buffer)
            self.input_buffer = ''
        # Desloca a pilha corretamente: T <- Z, Z <- Y, Y <- X
        self.T = self.Z
        print("agora t e:", self.T)
        self.Z = self.Y
        print("agora Z e:", self.Z)
        self.Y = self.X
        print("agora Y e:", self.Y)
        # NÃO alterar X aqui!
        self.stack_locked = False
        self.update_display()

    def add(self):
        self.ultimo_x = self.X
        if self.modo_programa_ativo:
            self.record_instruction(self.add)
        print("Calculando a soma...")
        resultado = self.Y + self.X
        self.X = resultado
        self.input_buffer = ""
        self.update_display()  # Atualiza o display após a operação

    def subtract(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.subtract)
        resultado = self.Y - self.X
        self.X = resultado
        self.update_display()

    def multiply(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.multiply)
        resultado = self.Y * self.X
        self.X = resultado
        self.update_display()

    def divide(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.divide)
        if self.X == 0:
            raise ZeroDivisionError("Divisão por zero")
        resultado = self.Y / self.X
        self.X = resultado
        self.update_display()

    def chs(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.chs)
        self.X = -self.X
        self.update_display()

    def clx(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.clx)
        self.X = 0.0
        self.input_buffer = ""
        self.stack_locked = False
        self.update_display()

    def c(self):
        if self.X == 0.0:
            self.clx()
        else:
            self.reg()

    def store_financial_value(self, key, value):
        if self.modo_programa_ativo:
            self.record_instruction(self.store_financial_value)
        self.vars[key] = value
        self.X = 0.0
        self.update_display()

    def calculate_i(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.calculate_i)
        print("calculando i (busca binária)...")
        n = self.vars.get("n")
        PV = self.vars.get("PV")
        PMT = self.vars.get("PMT")
        FV = self.vars.get("FV")

        if n == 0:
            raise ValueError("Número de períodos não pode ser zero.")

        def f(r):
            try:
                return PV + PMT * ((1 - (1 + r) ** -n) / r) + FV / ((1 + r) ** n)
            except:
                return float("inf")

        low = 0.000001
        high = 10.0
        tol = 1e-7
        max_iter = 100

        for _ in range(max_iter):
            mid = (low + high) / 2
            f_mid = f(mid)

            if not math.isfinite(f_mid):
                high = mid
                continue

            if abs(f_mid) < tol:
                result = round(mid * 100, 5)
                self.vars["i"] = result
                self.X = result
                self.update_display()
                return

            if f(low) * f_mid < 0:
                high = mid
            else:
                low = mid

        raise ValueError("Não foi possível encontrar a taxa de juros.")

    def calculate_n(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.calculate_n)
        i = self.vars["i"] / 100
        PV, PMT, FV = self.vars["PV"], self.vars["PMT"], self.vars["FV"]
        if i == 0: raise ValueError("Taxa de juros não pode ser zero.")
        num = -(PV + PMT / i)
        den = FV + PMT / i
        n = math.log(num / den) / math.log(1 + i)
        self.vars["n"] = round(n, 5)
        self.X = self.vars["n"]
        self.update_display()

    def calculate_pv(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.calculate_pv)
        n = self.vars["n"]
        i = self.vars["i"] / 100
        PMT = self.vars["PMT"]
        FV = self.vars["FV"]
        if i == 0: raise ValueError("Taxa de juros não pode ser zero.")
        PV = -PMT * ((1 - (1 + i) ** -n) / i) - FV / ((1 + i) ** n)
        self.vars["PV"] = round(PV, 5)
        self.X = self.vars["PV"]
        self.update_display()

    def calculate_pmt(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.calculate_pmt)
        n = self.vars["n"]
        i = self.vars["i"] / 100
        PV = self.vars["PV"]
        FV = self.vars["FV"]
        if i == 0: raise ValueError("Taxa de juros não pode ser zero.")
        PMT = -(PV * i + FV * i / ((1 + i) ** n)) / (1 - (1 + i) ** -n)
        self.vars["PMT"] = round(PMT, 5)
        self.X = self.vars["PMT"]
        self.update_display()

    def calculate_fv(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.calculate_fv)
        n = self.vars["n"]
        i = self.vars["i"] / 100
        PV = self.vars["PV"]
        PMT = self.vars["PMT"]
        if i == 0: raise ValueError("Taxa de juros não pode ser zero.")
        FV = -PV * ((1 + i) ** n) - PMT * (((1 + i) ** n - 1) / i)
        self.vars["FV"] = round(FV, 5)
        self.X = self.vars["FV"]
        self.update_display()

    def get_display(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.get_display)
        # Formatar número com a precisão definida
        format_str = f"{{:.{self.precision}f}}"
        formatted = format_str.format(self.X)

        # Separar parte inteira e decimal
        inteiro, _, decimal = formatted.partition('.')

        # Adicionar separador de milhar (ponto)
        inteiro_com_pontos = "{:,}".format(int(inteiro)).replace(",", ".")

        # Juntar novamente com a parte decimal
        final = f"{inteiro_com_pontos},{decimal}" if self.use_comma else f"{inteiro_com_pontos}.{decimal}"
        return final

    def push_number(self, digit):
        if self.modo_programa_ativo:
            self.record_instruction(lambda: self.push_number(digit))
        if self.stack_locked:
            self.enter()

        if hasattr(self, "entering_exponent") and self.entering_exponent:
            self.exponent_buffer += digit
            try:
                self.X *= 10 ** int(self.exponent_buffer)
            except ValueError:
                self.X = 0.0
            self.input_buffer = str(self.X)
            self.entering_exponent = False
            self.update_display()
            return

        self.input_buffer += digit
        try:
            self.X = float(self.input_buffer)
        except:
            self.X = 0.0
        print("Agora X é:", self.X)

        if self.waiting_for_sto_register:
            register = str(int(self.X))
            if register in self.memory:
                self.memory[register] = self.Y
                self.X = 0.0
                print(self.Y, "guardado na memória, casa:", register)
            else:
                raise ValueError(f"Registrador {register} inválido")
            self.waiting_for_sto_register = False

        if self.waiting_for_rcl_register:
            register = str(int(self.X))
            if register in self.memory:
                self.X = self.memory[register]
                self.update_display()
            else:
                raise ValueError(f"Registrador {register} inválido")
            self.waiting_for_rcl_register = False

        self.update_display()

    def backspace(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.backspace)
        self.input_buffer = self.input_buffer[:-1]
        self.X = float(self.input_buffer) if self.input_buffer else 0.0
        self.update_display()

    def clear(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.clear)
        self.stack = [0.0] * 4
        self.input_buffer = ''
        self.stack_locked = False
        self.update_display()

    def drop(self):
        if self.modo_programa_ativo:
            self.record_instruction(self.drop)
        self.X = self.Y
        self.Y = self.Z
        self.Z = self.T