from os import listdir
from time import strftime
import traceback

####################################################### VARIAVEIS GLOBAIS ###############################################################

URNA_TIPOS = ["null","SECAO","CONTINGENCIA","RESERVASECAO","RESERVAENCERRANDOSECAO"]
ARQUIVO_TIPOS = ["null", "votacaoUE","votacaoRED","saMistaMRParcialCedula","saMistaBUImpressoCedula","saManual","saEletronica"]
FASES = ["null","SIMULADO","OFICIAL","TREINAMENTO"]
CARGOS = ["null","PRESIDENTE","null","GOVERNADOR","null","SENADOR","DEPUTADO FEDERAL","DEPUTADO ESTADUAL"]
VOTO_TIPOS = ["null","LEGENDA","NOMINAL","BRANCO","NULO","BRANCOAPOSSUSPENSAO","NULOAPOSSUSPENSAO","NULOPORREPETICAO",\
               "NULOCARGOSEMCANDIDATO","NULOAPOSSUSPENSAOCARGOSEMCANDIDATO"]
CEDULA_TIPOS = ["null","MAJORITARIO","PROPORCIONAL"]
VOTO_ORIGENS = ["null","CEDULA","RDV","BU"]

CANDIDATOS = {27:"CLARIANA",13:"LULA",22:"FLAVIO",21:"EDMILSON",\
              70:"CURY",16:"HERTZ",14:"RENAN",\
              55:"CAIADO",29:"RUI",80:"SAMARA",35:"GRASSI",\
              30:"ZEMA"}

#########################################################################################################################################

############################################ FUNÇÕES PARA DECODIFICAÇÃO DE CAMPOS ASN.1 #################################################

def decodificarComprimento(sequencia):
    tag = sequencia[0]
    comprimento = sequencia[1]
    offset = 2
    if comprimento == 130:
        comprimento = int.from_bytes(sequencia[2:4],'big')
        offset = 4
    elif comprimento == 129:
        comprimento = int.from_bytes(sequencia[2:3],'big')
        offset = 3
    return offset

def lerCampo(sequencia,offset):
    tag = sequencia[offset]
    comprimento = sequencia[offset+1]
    inicio = offset + 2
    fim = offset + comprimento + 2
    if comprimento == 130:
        comprimento = int.from_bytes(sequencia[offset+2:offset+4],'big')
        fim = offset + comprimento + 4
        inicio = inicio + 2
    elif comprimento == 129:
        comprimento = int.from_bytes(sequencia[offset+2:offset+3],'big')
        fim = offset + comprimento + 3
        inicio = inicio + 1
    return sequencia[offset:fim],fim

def lerCampoPrimitivo(sequencia):
    tag = sequencia[0]
    comprimento = sequencia[1]
    inicio = 2
    fim = comprimento + 2
    if comprimento == 130:
        comprimento = int.from_bytes(sequencia[2:4],'big')
        fim = comprimento + 4
        inicio = inicio + 2
    elif comprimento == 129:
        comprimento = int.from_bytes(sequencia[2:3],'big')
        fim = comprimento + 3
        inicio = inicio + 1
    return sequencia[inicio:fim]

#########################################################################################################################################

########################################### FUNÇÕES PARA DECODIFICAÇÃO DOS CAMPOS DO RDV ################################################

def lerCamposResultadoRDV(dir_rdv):
    rdv = open(dir_rdv,"br")
    ResultadoRDV = rdv.read()
    rdv.close()

    inicio_cabecalho = decodificarComprimento(ResultadoRDV)
    Cabecalho,inicio_urna = lerCampo(ResultadoRDV,inicio_cabecalho)
    Urna,inicio_rdv = lerCampo(ResultadoRDV,inicio_urna)
    Rdv,final = lerCampo(ResultadoRDV,inicio_rdv)

    return Cabecalho,Urna,Rdv

def lerCamposCabecalho(Cabecalho):
    inicio_dataGeracao = decodificarComprimento(Cabecalho)
    dataGeracao,inicio_idEleitoral = lerCampo(Cabecalho,inicio_dataGeracao)
    idEleitoral,final = lerCampo(Cabecalho,inicio_idEleitoral)

    return dataGeracao,idEleitoral

def lerCamposUrna(Urna):
    inicio_tipoUrna = decodificarComprimento(Urna)
    tipoUrna,inicio_versaoVotacao = lerCampo(Urna,inicio_tipoUrna)
    versaoVotacao,inicio_correspondenciaResultado = lerCampo(Urna,inicio_versaoVotacao)
    correspondenciaResultado,inicio_tipoArquivo = lerCampo(Urna,inicio_correspondenciaResultado)
    tipoArquivo,inicio_numeroSerieFV = lerCampo(Urna,inicio_tipoArquivo)
    numeroSerieFV,final = lerCampo(Urna,inicio_numeroSerieFV)

    return tipoUrna,versaoVotacao,correspondenciaResultado,tipoArquivo,numeroSerieFV

def lerCamposCorrespondenciaResultado(correspondenciaResultado):
    inicio_identificacao = decodificarComprimento(correspondenciaResultado)
    identificacao,inicio_carga = lerCampo(correspondenciaResultado,inicio_identificacao)
    carga,final = lerCampo(correspondenciaResultado,inicio_carga)

    return identificacao,carga

def lerCamposIdentificacao(identificacao):
    inicio_municipioZona = decodificarComprimento(identificacao)
    municipioZona,inicio_local = lerCampo(identificacao,inicio_municipioZona)
    local,inicio_secao = lerCampo(identificacao,inicio_local)
    secao,final = lerCampo(identificacao,inicio_secao)

    return municipioZona,local,secao

def lerCamposMunicipioZona(municipioZona):
    inicio_municipio = decodificarComprimento(municipioZona)
    municipio,inicio_zona = lerCampo(municipioZona,inicio_municipio)
    zona,final = lerCampo(municipioZona,inicio_zona)

    return municipio,zona

def lerCamposCarga(carga):
    inicio_numeroInternoUrna = decodificarComprimento(carga)
    numeroInternoUrna,inicio_numeroSerieFC = lerCampo(carga,inicio_numeroInternoUrna)
    numeroSerieFC,inicio_identificadorGeradorMidia = lerCampo(carga,inicio_numeroSerieFC)
    identificadorGeradorMidia,inicio_dataHoraCarga = lerCampo(carga,inicio_identificadorGeradorMidia)
    dataHoraCarga,inicio_codigoCarga = lerCampo(carga,inicio_dataHoraCarga)
    codigoCarga,final = lerCampo(carga,inicio_codigoCarga)

    return numeroInternoUrna,numeroSerieFC,identificadorGeradorMidia,dataHoraCarga,codigoCarga

def lerCamposIdentificadorGeradorMidia(identificadorGeradorMidia):
    inicio_nome = decodificarComprimento(identificadorGeradorMidia)
    nome,inicio_serialCertificadoTPM = lerCampo(identificadorGeradorMidia,inicio_nome)
    serialCertificadoTPM,inicio_serialInstalacao = lerCampo(identificadorGeradorMidia,inicio_serialCertificadoTPM)
    serialInstalacao,final = lerCampo(identificadorGeradorMidia,inicio_serialInstalacao)

    return nome,serialCertificadoTPM,serialInstalacao

def lerCamposRdv(Rdv):
    inicio_pleito = decodificarComprimento(Rdv)
    pleito,inicio_fase = lerCampo(Rdv,inicio_pleito)
    fase,inicio_identificacao = lerCampo(Rdv,inicio_fase)
    identificacao,inicio_historicoCodigosCarga = lerCampo(Rdv,inicio_identificacao)
    historicoCodigosCarga,inicio_eleicoes = lerCampo(Rdv,inicio_historicoCodigosCarga)
    eleicoes,final = lerCampo(Rdv,inicio_eleicoes)

    return pleito,fase,identificacao,historicoCodigosCarga,eleicoes

def lerCamposHistoricoCodigosCarga(historicoCodigosCarga):
    tamanho_historico = historicoCodigosCarga[1]
    if tamanho_historico == 130:
        tamanho_historico = int.from_bytes(historicoCodigosCarga[2:4],'big')
    elif tamanho_historico == 129:
        tamanho_historico = int.from_bytes(historicoCodigosCarga[2:3],'big')
    historico = []
    inicio_codigoCarga = decodificarComprimento(historicoCodigosCarga)
    codigoCarga,final = lerCampo(historicoCodigosCarga,inicio_codigoCarga)
    tamanho_codigo = len(codigoCarga)
    dif = tamanho_historico-tamanho_codigo
    historico.append(codigoCarga)
    while dif != 0:
        codigoCarga,final = lerCampo(historicoCodigosCarga,final)
        historico.append(codigoCarga)
        tamanho_codigo = tamanho_codigo + len(codigoCarga)
        dif = tamanho_historico - tamanho_codigo
    return historico

def lerCamposEleicoes(eleicoes):
    if eleicoes[0] == 161:
        tamanho_seq = eleicoes[1]
        if tamanho_seq == 130:
            tamanho_seq = int.from_bytes(eleicoes[2:4],'big')
        elif tamanho_seq == 129:
            tamanho_seq = int.from_bytes(eleicoes[2:3],'big')
        seqEleicoes = []
        inicio_eleicaoVota = decodificarComprimento(eleicoes)
        eleicaoVota,final = lerCampo(eleicoes,inicio_eleicaoVota)
        tamanho_eleicao = len(eleicaoVota)
        dif = tamanho_seq - tamanho_eleicao
        seqEleicoes.append(eleicaoVota)
        while dif != 0:
            eleicaoVota,final = lerCampo(eleicoes,final)
            tamanho_eleicao = tamanho_eleicao + len(eleicaoVota)
            dif = tamanho_seq - tamanho_eleicao
            seqEleicoes.append(eleicaoVota)
        return seqEleicoes,1
    elif eleicoes[0] == 162:
        tamanho_seq = eleicoes[1]
        if tamanho_seq == 130:
            tamanho_seq = int.from_bytes(eleicoes[2:4],'big')
        elif tamanho_seq == 129:
            tamanho_seq = int.from_bytes(eleicoes[2:3],'big')
        seqEleicoes = []
        inicio_eleicaoSA = decodificarComprimento(eleicoes)
        eleicaoSA,final = lerCampo(eleicoes,inicio_eleicaoSA)
        tamanho_eleicao = len(eleicaoSA)
        dif = tamanho_seq - tamanho_eleicao
        seqEleicoes.append(eleicaoSA)
        while dif != 0:
            eleicaoSA,final = lerCampo(eleicoes,final)
            tamanho_eleicao = tamanho_eleicao + len(eleicaoSA)
            dif = tamanho_seq - tamanho_eleicao
            seqEleicoes.append(eleicaoSA)
        return seqEleicoes,2

def lerCamposEleicaoVota(eleicaoVota):
    inicio_idEleicao = decodificarComprimento(eleicaoVota)
    idEleicao,inicio_votosCargos = lerCampo(eleicaoVota,inicio_idEleicao)
    votosCargos,final = lerCampo(eleicaoVota,inicio_votosCargos)

    return idEleicao,votosCargos

def lerCamposEleicaoSA(eleicaoSA):
    inicio_idEleicao = decodificarComprimento(eleicaoSA)
    idEleicao,inicio_tipoCedulaSA = lerCampo(eleicaoSA,inicio_idEleicao)
    tipoCedulaSA,inicio_origemVotosSA = lerCampo(eleicaoSA,inicio_tipoCedulaSA)
    origemVotosSA,inicio_votosCargos = lerCampo(eleicaoSA,inicio_origemVotosSA)
    votosCargos,final = lerCampo(eleicaoSA,inicio_votosCargos)

    return idEleicao,tipoCedulaSA,origemVotosSA,votosCargos

def lerVotosCargo(votosCargos):
    inicio_votosCargo = decodificarComprimento(votosCargos)
    votosCargo,final = lerCampo(votosCargos,inicio_votosCargo)

    return votosCargo

def lerVotosPresidente(votosCargo):
    inicio_idCargo = decodificarComprimento(votosCargo)
    idCargo,inicio_quantidadeEscolhas = lerCampo(votosCargo,inicio_idCargo)
    quantidadeEscolhas,inicio_votos = lerCampo(votosCargo,inicio_quantidadeEscolhas)
    votos,final = lerCampo(votosCargo,inicio_votos)

    return idCargo,quantidadeEscolhas,votos

def listarVotos(votos):
    tamanho_lista = votos[1]
    if tamanho_lista == 130:
        tamanho_lista = int.from_bytes(votos[2:4],'big')
    elif tamanho_lista == 129:
        tamanho_lista = int.from_bytes(votos[2:3],'big')
    listaVotos = []
    inicio_voto = decodificarComprimento(votos)
    voto,final = lerCampo(votos,inicio_voto)
    tamanho_voto = len(voto)
    dif = tamanho_lista-tamanho_voto
    listaVotos.append(voto)
    while dif != 0:
        voto,final = lerCampo(votos,final)
        listaVotos.append(voto)
        tamanho_voto = tamanho_voto + len(voto)
        dif = tamanho_lista - tamanho_voto
    return listaVotos

#########################################################################################################################################

######################################################## EXTRATOR DOS CAMPOS DO RDV #####################################################

def extrairRDV(dir_rdv):
    Cabecalho,Urna,Rdv = lerCamposResultadoRDV(dir_rdv)
    dataGeracao,idEleitoral = lerCamposCabecalho(Cabecalho)
    dataGeracao = lerCampoPrimitivo(dataGeracao)
    idEleitoral = int.from_bytes(lerCampoPrimitivo(idEleitoral),'big')

    tipoUrna,versaoVotacao,correspondenciaResultado,tipoArquivo,numeroSerieFV = lerCamposUrna(Urna)
    tipoUrna = URNA_TIPOS[int.from_bytes(lerCampoPrimitivo(tipoUrna),'big')]
    versaoVotacao = lerCampoPrimitivo(versaoVotacao)
    tipoArquivo = ARQUIVO_TIPOS[int.from_bytes(lerCampoPrimitivo(tipoArquivo),'big')]
    numeroSerieFV = lerCampoPrimitivo(numeroSerieFV)
    identificacao,carga = lerCamposCorrespondenciaResultado(correspondenciaResultado)
    municipioZona,local,secao = lerCamposIdentificacao(identificacao)
    municipio,zona = lerCamposMunicipioZona(municipioZona)
    municipio = int.from_bytes(lerCampoPrimitivo(municipio),'big')
    zona = int.from_bytes(lerCampoPrimitivo(zona),'big')
    local = int.from_bytes(lerCampoPrimitivo(local),'big')
    secao = int.from_bytes(lerCampoPrimitivo(secao),'big')
    numeroInternoUrna,numeroSerieFC,identificadorGeradorMidia,dataHoraCarga,codigoCarga = lerCamposCarga(carga)
    numeroInternoUrna = int.from_bytes(lerCampoPrimitivo(numeroInternoUrna),'big')
    numeroSerieFC = lerCampoPrimitivo(numeroSerieFC)
    nome,serialCertificadoTPM,serialInstalacao = lerCamposIdentificadorGeradorMidia(identificadorGeradorMidia)
    nome = lerCampoPrimitivo(nome)
    serialCertificadoTPM = lerCampoPrimitivo(serialCertificadoTPM)
    serialInstalacao = lerCampoPrimitivo(serialInstalacao)
    dataHoraCarga = lerCampoPrimitivo(dataHoraCarga)
    codigoCarga = lerCampoPrimitivo(codigoCarga)

    pleito,fase,identificacao,historicoCodigosCarga,eleicoes = lerCamposRdv(Rdv)
    pleito = int.from_bytes(lerCampoPrimitivo(pleito),'big')
    fase = FASES[int.from_bytes(lerCampoPrimitivo(fase),'big')]
    municipioZona,local,secao = lerCamposIdentificacao(identificacao)
    municipio,zona = lerCamposMunicipioZona(municipioZona)
    municipio = int.from_bytes(lerCampoPrimitivo(municipio),'big')
    zona = int.from_bytes(lerCampoPrimitivo(zona),'big')
    local = int.from_bytes(lerCampoPrimitivo(local),'big')
    secao = int.from_bytes(lerCampoPrimitivo(secao),'big')
    historico = lerCamposHistoricoCodigosCarga(historicoCodigosCarga)
        
    historicoCarga = []
    for codigo in historico:
        carga = lerCampoPrimitivo(codigo)
        historicoCarga.append(carga)

    listaEleicoes,choice = lerCamposEleicoes(eleicoes)
    if choice == 1:
        listaIdVotos = []
        for eleicaoVota in listaEleicoes:
            idEleicao,votosCargos = lerCamposEleicaoVota(eleicaoVota)
            idEleicao = int.from_bytes(lerCampoPrimitivo(idEleicao),'big')
            listaIdVotos.append([idEleicao,votosCargos])
    elif choice == 2:
        listaIdVotos = []
        for eleicaoSA in listaEleicoes:
            idEleicao,tipoCedulaSA,origemVotosSA,votosCargos = lerCamposEleicaoSA(eleicaoSA)
            idEleicao = int.from_bytes(lerCampoPrimitivo(idEleicao),'big')
            tipoCedulaSA = CEDULA_TIPOS[int.from_bytes(lerCampoPrimitivo(tipoCedulaSA),'big')]
            origemVotosSA = VOTO_ORIGENS[int.from_bytes(lerCampoPrimitivo(origemVotosSA),'big')]
            listaIdVotos.append([idEleicao,tipoCedulaSA,origemVotosSA,votosCargos])
    listaVotos = []
    for idVotos in listaIdVotos:
        if len(idVotos) == 2:
            votosCargos = idVotos[1]
        elif len(idVotos) == 4:
            votosCargos = idVotos[3]
        votos = lerVotosCargo(votosCargos)
        idCargo,quantidadeEscolhas,v = lerVotosPresidente(votos)
        if v[1] == 0:
            continue
        ind = int.from_bytes(lerCampoPrimitivo(idCargo),'big')
        if ind not in [1,3,5,6,7]:
            continue
        idCargo = CARGOS[ind]
        quantidadeEscolhas = int.from_bytes(lerCampoPrimitivo(quantidadeEscolhas),'big')
        if idCargo == "PRESIDENTE":
            listaVotos = listaVotos + listarVotos(v)
    
    return dataGeracao,idEleitoral,tipoUrna,versaoVotacao,tipoArquivo,\
           numeroSerieFV,municipio,zona,local,secao,numeroInternoUrna,\
           numeroSerieFC,nome,serialCertificadoTPM,serialInstalacao,\
           dataHoraCarga,codigoCarga,pleito,fase,municipio,zona,local,secao,\
           historico,listaVotos

#########################################################################################################################################

################################################# DECODIFICADOR E CONTABILIZADOR DE VOTOS ###############################################

def decodificarVoto(voto):
    tipoVoto = voto[4]
    if len(voto) == 9:
        votoDigitado = int(voto[7:9],10)
    else:
        votoDigitado = None
    return tipoVoto,votoDigitado

def contabilizarVotos(listaVotos):
    total = 0
    validos = 0
    VOTOS = {"BRANCOS":0,"NULOS":0,"LULA":0,"FLAVIO":0,"CLARIANA":0,\
             "EDMILSON":0,"CURY":0,"HERTZ":0,"RENAN":0,\
             "CAIADO":0,"RUI":0,"SAMARA":0,"GRASSI":0,"ZEMA":0}
    for voto in listaVotos:
        total = total + 1
        tipo,numero = decodificarVoto(voto)
        if tipo in [3,5]:
            VOTOS["BRANCOS"] = VOTOS["BRANCOS"] + 1
            continue
        elif tipo in [4,6,7,8,9]:
            VOTOS["NULOS"] = VOTOS["NULOS"] + 1
        elif tipo == 2:
            if numero == 28:
                VOTOS["NULOS"] = VOTOS["NULOS"] + 1 # JÁ FOI LEVADA EM CONSIDERACAO A DESISTENCIA DO CANDIDATO AVALANCHE (28)
            else:
                validos = validos + 1
                VOTOS[CANDIDATOS[numero]] = VOTOS[CANDIDATOS[numero]] + 1
    return VOTOS,total,validos

#########################################################################################################################################

################################################### TOTALIZADOR POR ESTADO ##############################################################

def totalizarEstado(uf,dir_rdv,dir_relatorio):
    dir_uf = dir_rdv + uf + "/"
    lista_municipios = listdir(dir_uf)
    lista_municipios.sort()
    dir_relatorio = dir_relatorio + "relatorio" + "_" + uf + "_" + \
                  strftime("%H%M%S%d%m%Y")
    relatorio = open(dir_relatorio,"w")
    TOTAL_GLOBAL = 0
    VALIDOS_GLOBAL = 0
    NULOS_GLOBAL = 0
    BRANCOS_GLOBAL = 0
    LULA_GLOBAL = 0
    FLAVIO_GLOBAL = 0
    SECOES = 0
    for municipio in lista_municipios:
        dir_municipio = dir_uf + municipio + "/"
        lista_zonas = listdir(dir_municipio)
        for zona in lista_zonas:
            dir_zona = dir_municipio + zona + "/"
            lista_secoes = listdir(dir_zona)
            for secao in lista_secoes:
                SECOES = SECOES + 1
                dir_secao = dir_zona + secao + "/"
                lista_pastas_rdv = listdir(dir_secao)
                for pasta_rdv in lista_pastas_rdv:
                    dir_rdv = dir_secao + pasta_rdv + "/"
                    arquivos_rdv = listdir(dir_rdv)
                    for arquivo_rdv in arquivos_rdv:
                        dir_rdv = dir_rdv + arquivo_rdv
                        try:
                            RDV = extrairRDV(dir_rdv)
                        except:
                            print(dir_rdv)
                            traceback.print_exc()
                        rdv_string0 = "URNA:"+str(RDV[10])+"::"
                        rdv_string1 = "TIPO:"+str(RDV[2])+"::"
                        rdv_string2 = "MUNICIPIO:"+str(RDV[19])+"::"
                        rdv_string3 = "ZONA:"+str(RDV[20])+"::"
                        rdv_string4 = "SECAO:"+str(RDV[22])+"::"
                        relatorio.write(rdv_string0+rdv_string1+rdv_string2+rdv_string3+rdv_string4)
                        listaVotos = RDV[24]
                        contabilizacao,total,validos = contabilizarVotos(listaVotos)
                        for candidato in contabilizacao:
                            relatorio.write(candidato + ":" + str(contabilizacao[candidato]) + "::")
                            if candidato == "LULA":
                                LULA_GLOBAL = LULA_GLOBAL + contabilizacao[candidato]
                            elif candidato == "FLAVIO":
                                FLAVIO_GLOBAL = FLAVIO_GLOBAL + contabilizacao[candidato]
                            elif candidato == "BRANCOS":
                                BRANCOS_GLOBAL = BRANCOS_GLOBAL + contabilizacao[candidato]
                            elif candidato == "NULOS":
                                NULOS_GLOBAL = NULOS_GLOBAL + contabilizacao[candidato]
                        relatorio.write("VOTOS APURADOS:"+str(total)+"::")
                        relatorio.write("VOTOS VALIDOS:"+str(validos)+"::")
                        TOTAL_GLOBAL = TOTAL_GLOBAL + total
                        VALIDOS_GLOBAL = VALIDOS_GLOBAL + validos
                        relatorio.write("::::")
    relatorio.write("SECOES APURADAS:" + str(SECOES) + "::")
    relatorio.write("TOTAL DE VOTOS APURADOS:" + str(TOTAL_GLOBAL) + "::")
    relatorio.write("TOTAL DE VOTOS VALIDOS:" + str(VALIDOS_GLOBAL) + "::")
    relatorio.write("TOTAL DE VOTOS BRANCOS:" + str(BRANCOS_GLOBAL) + "::")
    relatorio.write("TOTAL DE VOTOS NULOS:" + str(NULOS_GLOBAL) + "::")
    relatorio.write("TOTAL DE VOTOS LULA:" + str(LULA_GLOBAL) + "::")
    relatorio.write("TOTAL DE VOTOS FLAVIO:" + str(FLAVIO_GLOBAL) + "::")
    porcentagem_lula = f"{100*LULA_GLOBAL/VALIDOS_GLOBAL:.2f}"
    porcentagem_flavio = f"{100*FLAVIO_GLOBAL/VALIDOS_GLOBAL:.2f}"
    relatorio.write("PORCENTAGEM LULA:" + porcentagem_lula + "%::")
    relatorio.write("PORCENTAGEM FLAVIO:" + porcentagem_flavio + "%::")
    relatorio.close()

    return SECOES,TOTAL_GLOBAL,VALIDOS_GLOBAL,BRANCOS_GLOBAL,NULOS_GLOBAL,LULA_GLOBAL,FLAVIO_GLOBAL

#########################################################################################################################################

############################################################### TESTES ##################################################################

################################################## TESTE 1: EXTRAIR RDV INDIVIDUALMENTE #################################################

def teste1():
    dir_rdv = input("Digite o caminho do RDV: ")

    rdv = extrairRDV(dir_rdv)
    print("dataGeracao:",rdv[0])
    print("idEleitoral:",rdv[1])
    print("tipoUrna:",rdv[2])
    print("versaoVotacao:",rdv[3])
    print("tipoArquivo:",rdv[4])
    print("numeroSerieFV:",rdv[5])
    print("municipio:",rdv[6])
    print("zona:",rdv[7])
    print("local:",rdv[8])
    print("secao:",rdv[9])
        
    print("numeroInternoUrna:",rdv[10])
    print("numeroSerieFC:",rdv[11])
    print("nome:",rdv[12])
    print("serialCertificadoTPM:",rdv[13])
    print("serialInstalacao:",rdv[14])

    print("dataHoraCarga:",rdv[15])
    print("codigoCarga:",rdv[16])
    print("pleito:",rdv[17])
    print("fase:",rdv[18])
    print("municipio:",rdv[19])
    print("zona:",rdv[20])
    print("local:",rdv[21])
    print("secao:",rdv[22])
    print("historicoCodigosCarga:",rdv[23])
    print("listaVotos:",rdv[24])

    print(contabilizarVotos(rdv[24]))

    return

#########################################################################################################################################

###################################################### TESTE 2: TOTALIZAR UM ESTADO #####################################################

def teste2():
    uf = input("Entre com a sigla da UF (letras minusculas): ")
    dir_rdv = input("Digite o caminho da pasta raiz que contém os RDVs: ")
    dir_relatorio = input("Digite o caminho da pasta para armazenar o relatorio da totalizacao: ")
    s,t,v,b,n,l,f = totalizarEstado(uf,dir_rdv,dir_relatorio)
    s = f"{s:,}".replace(",", ".")
    t = f"{t:,}".replace(",", ".")
    v = f"{v:,}".replace(",", ".")
    b = f"{b:,}".replace(",", ".")
    n = f"{n:,}".replace(",", ".")
    l = f"{l:,}".replace(",", ".")
    f = f"{f:,}".replace(",", ".")
    
    h = "   SECOES       TOTAL          VALIDOS        BRANCOS      NULOS        LULA          FLAVIO\n"
    print("\n\n" + h)
    print(uf,end = " ")
    k = 13 - len(str(s))
    print(s,end = k*" ")
    k = 15 - len(str(t))
    print(t,end = k*" ")
    k = 15 - len(str(v))
    print(v,end = k*" ")
    k = 13 - len(str(b))
    print(b,end = k*" ")
    k = 13 - len(str(n))
    print(n,end = k*" ")
    k = 14 - len(str(l))
    print(l,end = k*" ")
    k = 14 - len(str(f))
    print(f,end = k*" ")
    print("\n")


#########################################################################################################################################

################################################################# MAIN ##################################################################

def main():
    default_dir_rdv = "/home/dcomp/AUDITORIA/RDV/"
    default_dir_relatorio = "/home/dcomp/AUDITORIA/RELATORIOS/"
    
    definir_dir_rdv = int(input("Definir diretorio RDV? (0 = usar default; 1 = definir) "))
    if definir_dir_rdv == 0:
        dir_rdv = default_dir_rdv
    elif definir_dir_rdv == 1:
        dir_rdv = input("Diretorio RDV: ")
    else:
        print("Opcao invalida!")
        return

    definir_dir_relatorio = int(input("Definir diretorio Relatorio? (0 = usar default; 1 = definir) "))
    if definir_dir_relatorio == 0:
        dir_relatorio = default_dir_relatorio
    elif definir_dir_relatorio == 1:
        dir_relatorio = input("Diretorio Relatorio: ")
    else:
        print("Opcao invalida!")
        return

    opcao = int(input("Escolha uma opcao (0 = totalizar todos os estados; 1 = extrair um RDV; 2 = totalizar um estado): "))
    if opcao == 0:
        lista_uf = listdir(dir_rdv)
        lista_uf.sort()
        secoes = 0
        total = 0
        validos = 0
        brancos = 0
        nulos = 0
        lula = 0
        flavio = 0
        h = "   SECOES       TOTAL          VALIDOS        BRANCOS      NULOS        LULA          FLAVIO\n"
        print("\n\n" + h)
        for uf in lista_uf:
            s,t,v,b,n,l,f = totalizarEstado(uf,dir_rdv,dir_relatorio)
            secoes = secoes + s
            total = total + t
            validos = validos + v
            brancos = brancos + b
            nulos = nulos + n
            lula = lula + l
            flavio = flavio + f
            
            # EXIBIR RESULTADOS:
            s = f"{s:,}".replace(",", ".")
            t = f"{t:,}".replace(",", ".")
            v = f"{v:,}".replace(",", ".")
            b = f"{b:,}".replace(",", ".")
            n = f"{n:,}".replace(",", ".")
            l = f"{l:,}".replace(",", ".")
            f = f"{f:,}".replace(",", ".")
            print(uf,end = " ")
            k = 13 - len(str(s))
            print(s,end = k*" ")
            k = 15 - len(str(t))
            print(t,end = k*" ")
            k = 15 - len(str(v))
            print(v,end = k*" ")
            k = 13 - len(str(b))
            print(b,end = k*" ")
            k = 13 - len(str(n))
            print(n,end = k*" ")
            k = 14 - len(str(l))
            print(l,end = k*" ")
            k = 14 - len(str(f))
            print(f,end = k*" ")
            print("\n")
            
        # GRAVAR RELATORIO DE TOTALIZACAO GLOBAL:
        relatorio_global = dir_relatorio + "relatorio_global" + "_" + \
                      strftime("%H%M%S%d%m%Y")
        relatorio = open(relatorio_global,"w")
        relatorio.write("TOTAL DE VOTOS APURADOS:" + str(total) + "\n")
        relatorio.write("TOTAL DE VOTOS VALIDOS:" + str(validos) + "\n")
        relatorio.write("TOTAL DE VOTOS BRANCOS:" + str(brancos) + "\n")
        relatorio.write("TOTAL DE VOTOS NULOS:" + str(nulos) + "\n")
        relatorio.write("TOTAL DE VOTOS PARA LULA:" + str(lula) + "\n")
        relatorio.write("TOTAL DE VOTOS PARA FLAVIO:" + str(flavio) + "\n\n")
        porcentagem_lula = f"{100*lula/validos:.2f}"
        porcentagem_flavio = f"{100*flavio/validos:.2f}"
        relatorio.write("LULA:" + str(porcentagem_lula) + "\n")
        relatorio.write("FLAVIO:" + str(porcentagem_flavio) + "\n")
        relatorio.close()
    elif opcao == 1:
        teste1()
    elif opcao == 2:
        teste2()
    else:
        print("Opcao invalida!")
        return

if __name__ == "__main__":
    main()



