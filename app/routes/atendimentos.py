from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.atendimento import Atendimento
import pandas as pd
from datetime import datetime
import traceback
import logging
import re
import sys
from functools import wraps
from io import BytesIO

bp = Blueprint('atendimentos', __name__)

def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            
            print("Erro na importação:", str(e))
            print("Traceback completo:")
            traceback.print_exc()
            
            
            return jsonify({
                'success': False,
                'message': 'Erro ao processar a importação',
                'error_details': str(e),
                'error_type': e.__class__.__name__
            }), 500
    
    return decorated_function

def log_error(e):
    """Função para logging detalhado de erros"""
    error_info = {
        'error_type': type(e).__name__,
        'error_message': str(e),
        'traceback': traceback.format_exc()
    }
    print("\n=== ERRO DETALHADO ===")
    print(f"Tipo do erro: {error_info['error_type']}")
    print(f"Mensagem: {error_info['error_message']}")
    print("Traceback completo:")
    print(error_info['traceback'])
    print("=====================\n")
    return error_info

@bp.route('/importar', methods=['GET', 'POST'])
@login_required
@handle_errors 
def importar():
    """
    O decorador handle_errors vai capturar qualquer erro não tratado
    e retornar uma resposta JSON apropriada
    """
    if request.method == 'POST':
        print("\n=== INICIANDO IMPORTAÇÃO ===")
        
        if 'file' not in request.files:
            print("Erro: Arquivo não encontrado no request")
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado',
                'error_details': 'O arquivo não foi enviado corretamente'
            })
        
        file = request.files['file']
        print(f"Arquivo recebido: {file.filename}")
        
        if not file or not file.filename:
            print("Erro: Nome do arquivo vazio")
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado',
                'error_details': 'O arquivo está vazio ou não tem nome'
            })

        
        temp_path = 'temp_upload.xlsx'
        file.save(temp_path)
        print(f"Arquivo salvo temporariamente em: {temp_path}")
        
        try:
            print("Tentando ler o arquivo Excel...")
            df = pd.read_excel(temp_path)
            print("DataFrame criado com sucesso")
            print(f"Shape: {df.shape}")
            print(f"Colunas: {list(df.columns)}")
            print("\nPrimeiras linhas do DataFrame:")
            print(df.head())
            print("\nTipos de dados:")
            print(df.dtypes)
            
        except Exception as e:
            log_error(e)
            return jsonify({
                'success': False,
                'message': 'Erro ao ler arquivo Excel',
                'error_details': str(e)
            })
        finally:
           
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        if df.empty:
            print("Erro: DataFrame vazio")
            return jsonify({
                'success': False,
                'message': 'Arquivo vazio',
                'error_details': 'O arquivo Excel não contém dados'
            })
        
        importados = 0
        erros = []
        
       
        colunas_necessarias = ['ORIGEM', 'PROTOCOLO', 'STATUS', 'MOTIVO', 'NOME', 'DATA']
        colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
        
        if colunas_faltantes:
            print(f"Erro: Colunas faltantes: {colunas_faltantes}")
            return jsonify({
                'success': False,
                'message': 'Colunas obrigatórias ausentes',
                'error_details': f'Faltam as colunas: {", ".join(colunas_faltantes)}'
            })

       
        for linha_excel, (_, row) in enumerate(df.iterrows(), start=2):
            print(f"\nProcessando linha {linha_excel}")
            
            try:
                print(f"Dados da linha: {dict(row)}")
                
              
                try:
                    data = pd.to_datetime(row['DATA'])
                    print(f"Data convertida: {data}")
                except Exception as e:
                    raise ValueError(f"Erro ao converter data: {str(e)}")
                
                atendimento_data = {
                    'origem': str(row['ORIGEM']).strip(),
                    'protocolo': str(row['PROTOCOLO']).strip(),
                    'status': str(row['STATUS']).strip(),
                    'nome_cliente': str(row['NOME']).strip(),
                    'data': data,
                    'atendente_id': current_user.id,
                    'motivo': str(row['MOTIVO']).strip()
                }
                
                
                if 'ATENDENTE' in row:
                    atendimento_data['atendente_responsavel'] = str(row['ATENDENTE']).strip()
                if 'DEPARTAMENTO' in row:
                    atendimento_data['departamento'] = str(row['DEPARTAMENTO']).strip()
                if 'NUMERO' in row:
                    atendimento_data['numero'] = str(row['NUMERO']).strip()
                
                print(f"Dados processados: {atendimento_data}")
                
                
                if Atendimento.query.filter_by(protocolo=atendimento_data['protocolo']).first():
                    raise ValueError("Protocolo já existe")
                
              
                atendimento = Atendimento(**atendimento_data)
                db.session.add(atendimento)
                importados += 1
                print(f"Linha {linha_excel} processada com sucesso")
                
            except Exception as e:
                print(f"Erro ao processar linha {linha_excel}: {str(e)}")
                erros.append({
                    'row': linha_excel,
                    'errors': [str(e)]
                })
                continue
        
        if importados > 0:
            try:
                print(f"\nTentando commit de {importados} registros...")
                db.session.commit()
                print("Commit realizado com sucesso")
                
                return jsonify({
                    'success': True,
                    'message': f'Importação concluída: {importados} registros importados com sucesso.',
                    'details': {
                        'total': len(df),
                        'success': importados,
                        'errors': erros
                    }
                })
            except Exception as e:
                db.session.rollback()
                log_error(e)
                return jsonify({
                    'success': False,
                    'message': 'Erro ao salvar no banco de dados',
                    'error_details': str(e)
                })
        else:
            print("Nenhum registro foi importado")
            return jsonify({
                'success': False,
                'message': 'Nenhum registro importado',
                'error_details': 'Todos os registros apresentaram erro',
                'details': {'errors': erros}
            })
    
    return render_template('atendimentos/import.html')

@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_atendimento():
    if request.method == 'POST':
        try:
            dados_atendimento = {
                'origem': request.form.get('origem'),
                'protocolo': request.form.get('protocolo'),
                'status': 'NOVO',
                'atendente_id': current_user.id,
                'atendente_responsavel': request.form.get('atendente_responsavel'),
                'suporte_adicional': request.form.get('suporte_adicional') if request.form.get('nivel') == '3' else None,
                'departamento': request.form.get('departamento'),
                'motivo': request.form.get('motivo'),
                'nome_cliente': request.form.get('nome_cliente'),
                'numero': request.form.get('numero'),
                'data': datetime.now(),
                'nivel': int(request.form.get('nivel', 1))
            }

            
            protocolo = dados_atendimento.get('protocolo')
            if protocolo and Atendimento.query.filter_by(protocolo=protocolo).first():
                flash('Protocolo já existe no sistema.', 'error')
                return redirect(url_for('atendimentos.novo_atendimento'))

            atendimento = Atendimento(**dados_atendimento)
            db.session.add(atendimento)
            db.session.commit()
            
            flash('Atendimento criado com sucesso!', 'success')
            return redirect(url_for('atendimentos.novo_atendimento'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar atendimento: {str(e)}', 'error')
            return redirect(url_for('atendimentos.novo_atendimento'))
        
        pass

    return render_template('atendimentos/create.html')

@bp.route('/listar')
@login_required
def listar():
   
    origem = request.args.get('origem')
    atendente_responsavel = request.args.get('atendente_responsavel') 
    nivel = request.args.get('nivel', type=int)
    status = request.args.get('status')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Atendimento.query
    
    if origem:
        query = query.filter(Atendimento.origem == origem)
    if atendente_responsavel:  
        query = query.filter(Atendimento.atendente_responsavel == atendente_responsavel)
    if nivel:
        query = query.filter(Atendimento.nivel == nivel)
    if status:
        query = query.filter(Atendimento.status == status)
    if data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(Atendimento.data.between(data_inicio, data_fim))
        except ValueError:
            flash('Formato de data inválido', 'error')
    
    page = request.args.get('page', 1, type=int)
    query = query.order_by(Atendimento.data.desc())
    atendimentos = query.paginate(page=page, per_page=10)
    
    return render_template('atendimentos/list.html',
                         atendimentos=atendimentos,
                         origem=origem,
                         atendente_responsavel=atendente_responsavel, 
                         nivel=nivel,
                         status=status,
                         data_inicio=data_inicio,
                         data_fim=data_fim)
    pass

@bp.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    atendimento = Atendimento.query.get_or_404(id)
    return render_template('atendimentos/view.html', atendimento=atendimento)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    atendimento = Atendimento.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            
            atendimento.origem = request.form.get('origem')
            atendimento.protocolo = request.form.get('protocolo')
            atendimento.departamento = request.form.get('departamento')
            atendimento.motivo = request.form.get('motivo')
            atendimento.nome_cliente = request.form.get('nome_cliente')
            atendimento.numero = request.form.get('numero')
            atendimento.nivel = int(request.form.get('nivel', 1))
            atendimento.atendente_responsavel = request.form.get('atendente_responsavel')
            
            if request.form.get('nivel') == '3':
                atendimento.suporte_adicional = request.form.get('suporte_adicional')
            else:
                atendimento.suporte_adicional = None
            
            db.session.commit()
            flash('Atendimento atualizado com sucesso!', 'success')
            return redirect(url_for('atendimentos.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar atendimento: {str(e)}', 'error')
            return redirect(url_for('atendimentos.editar', id=id))
    
   
    return render_template('atendimentos/edit.html', atendimento=atendimento)
    pass

@bp.route('/excluir/<int:id>', methods=['DELETE'])
@login_required
def excluir(id):
    try:
        atendimento = Atendimento.query.get_or_404(id)
        if not atendimento:
            return jsonify({
                'success': False,
                'message': 'Atendimento não encontrado'
            }), 404
            
        db.session.delete(atendimento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Atendimento excluído com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    pass

@bp.route('/exportar', methods=['GET'])  
@login_required
def exportar():
    try:
        origem = request.args.get('origem')
        atendente_responsavel = request.args.get('atendente_responsavel')
        nivel = request.args.get('nivel', type=int)
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Atendimento.query
        
        if origem:
            query = query.filter(Atendimento.origem == origem)
        if atendente_responsavel:
            query = query.filter(Atendimento.atendente_responsavel == atendente_responsavel)
        if nivel:
            query = query.filter(Atendimento.nivel == nivel)
        if status:
            query = query.filter(Atendimento.status == status)
        if data_inicio and data_fim:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(Atendimento.data.between(data_inicio, data_fim))
            except ValueError:
                flash('Formato de data inválido', 'error')
        
        atendimentos = query.order_by(Atendimento.data.desc()).all()
        
        dados = []
        for atendimento in atendimentos:
            dados.append({
                'ID': atendimento.id,
                'Origem': atendimento.origem,
                'Protocolo': atendimento.protocolo,
                'Status': atendimento.status,
                'Nível': atendimento.nivel,
                'Departamento': atendimento.departamento,
                'Motivo': atendimento.motivo,
                'Nome do Cliente': atendimento.nome_cliente,
                'Número': atendimento.numero,
                'Data': atendimento.data.strftime('%d/%m/%Y %H:%M:%S'),
                'Atendente Responsável': atendimento.atendente_responsavel,
                'Suporte Adicional': atendimento.suporte_adicional
            })
        
        df = pd.DataFrame(dados)
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Atendimentos', index=False)
            
            worksheet = writer.sheets['Atendimentos']
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                worksheet.set_column(i, i, max_length)
        
        output.seek(0)
        
        filename = f'atendimentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro na exportação: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro ao exportar dados',
            'error_details': str(e)
        }), 500