import pygame
import random
import sys
import os

# Inicialização do Pygame e do sistema de Joystick
pygame.init()
pygame.joystick.init()

# Configurações da Janela
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Combate Aéreo - Suporte Joystick")
relogio = pygame.time.Clock()

# Cores
COR_FUNDO = (20, 30, 45)
BRANCO = (255, 255, 255)
AZUL = (77, 173, 255)
VERMELHO = (255, 77, 77)
AMARELO = (255, 215, 0)
LARANJA = (255, 140, 0)

# Inicializar Joystick se disponível
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controle detectado: {joystick.get_name()}")
else:
    print("Nenhum controle USB detectado. Use o teclado (Setas + Espaço).")

# --- SISTEMA DE RANKING ---
ARQUIVO_RANKING = "ranking.txt"

def carregar_ranking():
    if not os.path.exists(ARQUIVO_RANKING):
        return []
    ranking = []
    with open(ARQUIVO_RANKING, "r") as f:
        for linha in f:
            if "," in linha:
                nome, pontos = linha.strip().split(",")
                ranking.append((nome, int(pontos)))
    return sorted(ranking, key=lambda x: x[1], reverse=True)[:5]

def salvar_pontuacao(nome, pontos):
    ranking = carregar_ranking()
    ranking.append((nome, pontos))
    ranking = sorted(ranking, key=lambda x: x[1], reverse=True)[:5]
    with open(ARQUIVO_RANKING, "w") as f:
        for n, p in ranking:
            f.write(f"{n},{p}\n")

# --- CLASSES DO JOGO ---
class AviaoJogador:
    def __init__(self):
        self.largura = 50
        self.altura = 50
        self.x = LARGURA // 2 - self.largura // 2
        self.y = ALTURA - 80
        self.velocidade = 6
        self.cooldown_tiro = 0

    def mover(self, dx, dy):
        self.x += dx * self.velocidade
        self.y += dy * self.velocidade
        # Limites da tela
        self.x = max(0, min(LARGURA - self.largura, self.x))
        self.y = max(0, min(ALTURA - self.altura, self.y))

    def atualizar(self):
        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1

    def desenhar(self):
        # Corpo do avião (triângulo)
        pygame.draw.polygon(tela, AZUL, [
            (self.x + self.largura // 2, self.y),
            (self.x, self.y + self.altura),
            (self.x + self.largura, self.y + self.altura)
        ])
        # Asas
        pygame.draw.rect(tela, AZUL, (self.x - 10, self.y + self.altura - 20, self.largura + 20, 8))

class Tiro:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocidade = -8
        self.largura = 6
        self.altura = 15

    def mover(self):
        self.y += self.velocidade

    def desenhar(self):
        pygame.draw.rect(tela, AMARELO, (self.x, self.y, self.largura, self.altura))

class AviaoInimigo:
    def __init__(self):
        self.largura = 40
        self.altura = 40
        self.x = random.randint(0, LARGURA - self.largura)
        self.y = -50
        self.velocidade = random.randint(2, 4)
        self.cooldown_bomba = random.randint(30, 90)

    def mover(self):
        self.y += self.velocidade

    def atualizar(self):
        if self.cooldown_bomba > 0:
            self.cooldown_bomba -= 1

    def desenhar(self):
        # Inimigo apontando para baixo
        pygame.draw.polygon(tela, VERMELHO, [
            (self.x + self.largura // 2, self.y + self.altura),
            (self.x, self.y),
            (self.x + self.largura, self.y)
        ])
        pygame.draw.rect(tela, VERMELHO, (self.x - 5, self.y + 10, self.largura + 10, 6))

class Bomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocidade = 5
        self.raio = 6

    def mover(self):
        self.y += self.velocidade

    def desenhar(self):
        pygame.draw.circle(tela, LARANJA, (self.x, self.y), self.raio)

# --- FUNÇÃO PRINCIPAL DO JOGO ---
def rodar_jogo():
    jogador = AviaoJogador()
    tiros = []
    inimigos = []
    bombas = []
    
    pontuacao = 0
    vidas = 3
    jogando = True

    while jogando:
        relogio.tick(60) # 60 FPS
        tela.fill(COR_FUNDO)

        # Captura de comandos do controle (eixos) e teclado
        dx, dy = 0, 0
        atirar = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 1. Inputs do Teclado
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:  dx = -1
        if teclas[pygame.K_RIGHT]: dx = 1
        if teclas[pygame.K_UP]:    dy = -1
        if teclas[pygame.K_DOWN]:  dy = 1
        if teclas[pygame.K_SPACE]: atirar = True

        # 2. Inputs do Joystick (Sobrescreve/Soma se houver comando)
        if joystick:
            # Analógico Esquerdo (Eixo 0 é Horizontal, Eixo 1 é Vertical)
            eixo_x = joystick.get_axis(0)
            eixo_y = joystick.get_axis(1)
            
            if abs(eixo_x) > 0.2: dx = eixo_x  # Deadzone contra drifts
            if abs(eixo_y) > 0.2: dy = eixo_y
            
            # Verifica os primeiros 4 botões de ação para atirar
            for b in range(min(joystick.get_numbuttons(), 4)):
                if joystick.get_button(b):
                    atirar = True

        # Movimentar jogador
        jogador.mover(dx, dy)
        jogador.atualizar()

        # Atirar
        if atirar and jogador.cooldown_tiro == 0:
            tiros.append(Tiro(jogador.x + jogador.largura // 2 - 3, jogador.y))
            jogador.cooldown_tiro = 15

        # Gerar Inimigos
        if random.random() < 0.02 and len(inimigos) < 6:
            inimigos.append(AviaoInimigo())

        # Atualizar e Desenhar Tiros
        for t in tiros[:]:
            t.mover()
            t.desenhar()
            if t.y < 0:
                tiros.remove(t)

        # Atualizar e Desenhar Inimigos
        for i in inimigos[:]:
            i.mover()
            i.atualizar()
            i.desenhar()

            # Inimigo joga bomba
            if i.cooldown_bomba == 0:
                bombas.append(Bomba(i.x + i.largura // 2, i.y + i.altura))
                i.cooldown_bomba = random.randint(60, 120)

            # Inimigo sai da tela
            if i.y > ALTURA:
                inimigos.remove(i)

           # Colisão Jogador vs Inimigo
            rect_jogador = pygame.Rect(jogador.x, jogador.y, jogador.largura, jogador.altura) # <-- Corrigido aqui!
            rect_inimigo = pygame.Rect(i.x, i.y, i.largura, i.altura)
            if rect_jogador.colliderect(rect_inimigo):
                inimigos.remove(i)
                vidas -= 1

        # Atualizar e Desenhar Bombas
        for b in bombas[:]:
            b.mover()
            b.desenhar()
            
            if b.y > ALTURA:
                bombas.remove(b)
                continue

            # Colisão Bomba vs Jogador
            rect_jogador = pygame.Rect(jogador.x, jogador.y, jogador.largura, jogador.altura)
            rect_bomba = pygame.Rect(b.x - b.raio, b.y - b.raio, b.raio*2, b.raio*2)
            if rect_jogador.colliderect(rect_bomba):
                bombas.remove(b)
                vidas -= 1

        # Colisões Tiro do Jogador vs Inimigo
        for t in tiros[:]:
            rect_tiro = pygame.Rect(t.x, t.y, t.largura, t.altura)
            for i in inimigos[:]:
                rect_inimigo = pygame.Rect(i.x, i.y, i.largura, i.altura)
                if rect_tiro.colliderect(rect_inimigo):
                    if t in tiros: tiros.remove(t)
                    inimigos.remove(i)
                    pontuacao += 10

        # Desenhar Jogador
        jogador.desenhar()

        # Interface de Texto (Pontuação e Vidas)
        fonte = pygame.font.SysFont("Arial", 24)
        txt_pontos = fonte.render(f"Pontos: {pontuacao}", True, BRANCO)
        txt_vidas = fonte.render(f"Vidas: {vidas}", True, VERMELHO)
        tela.blit(txt_pontos, (10, 10))
        tela.blit(txt_vidas, (10, 40))

        if vidas <= 0:
            jogando = False

        pygame.display.flip()

    tela_game_over(pontuacao)

# --- TELA DE FIM DE JOGO E RANKING ---
def tela_game_over(pontos_finais):
    ranking = carregar_ranking()
    entrou_no_ranking = len(ranking) < 5 or pontos_finais > ranking[-1][1]
    
    nome_jogador = ""
    escrevendo = entrou_no_ranking and pontos_finais > 0
    
    fonte = pygame.font.SysFont("Arial", 30)

    while True:
        tela.fill(COR_FUNDO)
        
        txt_fim = fonte.render("FIM DE JOGO", True, VERMELHO)
        txt_score = fonte.render(f"Sua Pontuação: {pontos_finais}", True, BRANCO)
        tela.blit(txt_fim, (LARGURA // 2 - txt_fim.get_width() // 2, 50))
        tela.blit(txt_score, (LARGURA // 2 - txt_score.get_width() // 2, 100))

        if escrevendo:
            txt_prompt = fonte.render("Novo Recorde! Digite seu nome: " + nome_jogador, True, AMARELO)
            tela.blit(txt_prompt, (LARGURA // 2 - txt_prompt.get_width() // 2, 160))
            txt_obs = fonte.render("[Pressione ENTER para Salvar]", True, BRANCO)
            tela.blit(txt_obs, (LARGURA // 2 - txt_obs.get_width() // 2, 210))
        else:
            # Exibir Ranking
            txt_rank_title = fonte.render("🏆 TOP 5 PILOTOS 🏆", True, AMARELO)
            tela.blit(txt_rank_title, (LARGURA // 2 - txt_rank_title.get_width() // 2, 180))
            
            ranking_atual = carregar_ranking()
            for idx, (nome, pts) in enumerate(ranking_atual):
                txt_item = fonte.render(f"{idx+1}. {nome} - {pts} pts", True, BRANCO)
                tela.blit(txt_item, (LARGURA // 2 - txt_item.get_width() // 2, 230 + idx * 35))
            
            txt_RESTART = fonte.render("Pressione ESPAÇO ou botão do controle para reiniciar", True, AZUL)
            tela.blit(txt_RESTART, (LARGURA // 2 - txt_RESTART.get_width() // 2, 480))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.KEYDOWN:
                if escrevendo:
                    if evento.key == pygame.K_RETURN and nome_jogador.strip() != "":
                        salvar_pontuacao(nome_jogador.strip(), pontos_finais)
                        escrevendo = False
                    elif evento.key == pygame.K_BACKSPACE:
                        nome_jogador = nome_jogador[:-1]
                    elif len(nome_jogador) < 10 and evento.unicode.isalnum():
                        nome_jogador += evento.unicode
                else:
                    if evento.key == pygame.K_SPACE:
                        return # Sai da tela de game over e volta pro loop principal
            
            # Controle para reiniciar
            if evento.type == pygame.JOYBUTTONDOWN and not escrevendo:
                return

        pygame.display.flip()
        relogio.tick(30)

# Loop principal do App
while True:
    rodar_jogo()