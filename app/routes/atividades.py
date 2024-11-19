from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.atividade_externa import AtividadeExterna
from datetime import datetime

bp = Blueprint('atividades', __name__)

@bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_atividade():
    if request.method == 'POST':
        try:
            hora_inicio = datetime.strptime(
                f"{request.form['data']} {request.form['hora_inicio']}", 
                '%Y-%m-%d %H:%M'
            )
            hora_fim = datetime.strptime(
                f"{request.form['data']} {request.form['hora_fim']}", 
                '%Y-%m-%d %H:%M'
            )
            
            atividade = AtividadeExterna()
            atividade.atendente_id = current_user.id
            atividade.atendente_nome = current_user.nome
            atividade.setor = request.form['setor']
            atividade.hora_inicio = hora_inicio
            atividade.hora_fim = hora_fim
            atividade.descricao = request.form['descricao']
            
            db.session.add(atividade)
            db.session.commit()
            
            flash('Atividade registrada com sucesso!', 'success')
            return redirect(url_for('atividades.nova_atividade'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar atividade: {str(e)}', 'error')
            
    page = request.args.get('page', 1, type=int)
    atendente_id = request.args.get('atendente')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    setor = request.args.get('setor')
    
    query = AtividadeExterna.query
    
    if data_inicio and data_fim:
        try:
            inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            fim = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(AtividadeExterna.hora_inicio.between(inicio, fim))
        except ValueError:
            flash('Formato de data inválido', 'error')
    
    if setor:
        query = query.filter(AtividadeExterna.setor == setor)
    
    atividades = query.order_by(AtividadeExterna.hora_inicio.desc()).paginate(
        page=page, per_page=10
    )
    
    return render_template('atividades/create.html', 
                         atividades=atividades,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         setor=setor)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_atividade(id):
    atividade = AtividadeExterna.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            hora_inicio = datetime.strptime(
                f"{request.form['data']} {request.form['hora_inicio']}", 
                '%Y-%m-%d %H:%M'
            )
            hora_fim = datetime.strptime(
                f"{request.form['data']} {request.form['hora_fim']}", 
                '%Y-%m-%d %H:%M'
            )
            
            atividade.setor = request.form['setor']
            atividade.hora_inicio = hora_inicio
            atividade.hora_fim = hora_fim
            atividade.descricao = request.form['descricao']
            
            db.session.commit()
            flash('Atividade atualizada com sucesso!', 'success')
            return redirect(url_for('atividades.nova_atividade'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar atividade: {str(e)}', 'error')
            
    return render_template('atividades/edit.html', atividade=atividade)

@bp.route('/excluir/<int:id>', methods=['DELETE'])
@login_required
def excluir_atividade(id):
    try:
        atividade = AtividadeExterna.query.get_or_404(id)
        db.session.delete(atividade)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Atividade excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400