"""Main application routes for dashboard, inbox and thread views."""

from __future__ import annotations

import io
import datetime as dt
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user

from ..extensions import db
from ..models import User, Thread, Email, Draft, Feedback
from ..forms import DraftForm
from ..utils import calculate_trust, translate_text, text_to_speech, pseudonymize


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Basic metrics
    user_threads = Thread.query.filter_by(user_id=current_user.id).all()
    total_emails = Email.query.join(Thread).filter(Thread.user_id == current_user.id).count()
    resolved = sum(1 for t in user_threads if t.resolved)
    pending = len(user_threads) - resolved
    urgent = sum(1 for t in user_threads if t.urgency)
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for t in user_threads:
        sentiments[t.sentiment] = sentiments.get(t.sentiment, 0) + 1
    avg_response_time = 0.0
    response_count = 0
    for t in user_threads:
        if t.draft and t.draft.is_sent:
            first_email_time = min(e.timestamp for e in t.emails)
            response_time = (t.draft.updated_at - first_email_time).total_seconds()
            avg_response_time += response_time
            response_count += 1
    avg_response_time = (avg_response_time / response_count / 60) if response_count else 0
    # Top threads by priority
    top_threads = sorted(user_threads, key=lambda th: th.priority_score, reverse=True)[:5]
    return render_template(
        'dashboard.html',
        total_emails=total_emails,
        resolved=resolved,
        pending=pending,
        urgent=urgent,
        sentiments=sentiments,
        avg_response_time=avg_response_time,
        top_threads=top_threads,
    )


@main_bp.route('/inbox')
@login_required
def inbox():
    threads = Thread.query.filter_by(user_id=current_user.id).order_by(Thread.updated_at.desc()).all()
    return render_template('inbox.html', threads=threads)


@main_bp.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
@login_required
def thread_view(thread_id: int):
    thread = Thread.query.get_or_404(thread_id)
    if thread.user_id != current_user.id:
        flash('You do not have access to this thread.', 'danger')
        return redirect(url_for('main.inbox'))
    draft = thread.draft
    form = DraftForm()
    if form.validate_on_submit():
        # Update draft with edited text
        if not draft:
            flash('No draft available to send.', 'danger')
            return redirect(url_for('main.thread_view', thread_id=thread_id))
        draft.reply_text = form.reply_text.data
        draft.tone = form.tone.data
        # Convert to selected language
        if form.language.data != 'en':
            draft.reply_text = translate_text(draft.reply_text, form.language.data)
        draft.is_sent = True
        draft.updated_at = dt.datetime.utcnow()
        thread.resolved = True
        db.session.commit()
        flash('Reply sent (simulated).', 'success')
        return redirect(url_for('main.thread_view', thread_id=thread_id))
    return render_template('thread.html', thread=thread, draft=draft, form=form)


@main_bp.route('/tts/<int:draft_id>')
@login_required
def tts(draft_id: int):
    draft = Draft.query.get_or_404(draft_id)
    data = text_to_speech(draft.reply_text, draft.tone)
    return send_file(io.BytesIO(data), mimetype='audio/wav', as_attachment=True, download_name='reply.wav')