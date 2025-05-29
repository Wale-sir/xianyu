from flask import Blueprint, jsonify, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from models.relationship import Relationship, Message
from models.user import User

social_bp = Blueprint('social', __name__, url_prefix='/social')

@social_bp.route('/follow/<user_id>', methods=['POST'])
@login_required
def follow(user_id):
    try:
        if current_user.id == user_id:
            flash('不能关注自己')
            return redirect(url_for('auth.profile', user_id=user_id))
            
        if Relationship.is_following(current_user.id, user_id):
            flash('你已经关注了该用户')
        else:
            if Relationship.follow(current_user.id, user_id):
                flash('关注成功！')
            else:
                flash('关注失败，请重试')
    except Exception as e:
        print(f"Error following user: {str(e)}")
        flash('关注失败，请重试')
    return redirect(url_for('auth.profile', user_id=user_id))

@social_bp.route('/unfollow/<user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    try:
        if current_user.id == user_id:
            flash('不能取消关注自己')
            return redirect(url_for('auth.profile', user_id=user_id))
            
        if not Relationship.is_following(current_user.id, user_id):
            flash('你还没有关注该用户')
        else:
            if Relationship.unfollow(current_user.id, user_id):
                flash('取消关注成功！')
            else:
                flash('取消关注失败，请重试')
    except Exception as e:
        print(f"Error unfollowing user: {str(e)}")
        flash('取消关注失败，请重试')
    return redirect(url_for('auth.profile', user_id=user_id))

@social_bp.route('/followers')
@login_required
def followers():
    try:
        follower_ids = Relationship.get_followers(current_user.id)
        followers = [User.get_by_id(fid) for fid in follower_ids]
        return render_template('social/followers.html', followers=followers)
    except Exception as e:
        print(f"Error getting followers: {str(e)}")
        flash('获取粉丝列表失败')
        return redirect(url_for('auth.profile'))

@social_bp.route('/following')
@login_required
def following():
    try:
        following_ids = Relationship.get_following(current_user.id)
        following = [User.get_by_id(fid) for fid in following_ids]
        return render_template('social/following.html', following=following)
    except Exception as e:
        print(f"Error getting following: {str(e)}")
        flash('获取关注列表失败')
        return redirect(url_for('auth.profile'))

@social_bp.route('/messages')
@login_required
def messages():
    try:
        # 获取所有对话
        conversations = []
        messages = Message.get_conversations(current_user.id)
        for msg in messages:
            other_user = User.get_by_id(msg['other_user_id'])
            if other_user:
                conversations.append({
                    'user': other_user,
                    'last_message': msg['last_message'],
                    'unread_count': msg['unread_count']
                })
        return render_template('social/messages.html', conversations=conversations)
    except Exception as e:
        print(f"Error getting messages: {str(e)}")
        flash('获取消息列表失败')
        return redirect(url_for('auth.profile'))

@social_bp.route('/messages/<user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    try:
        if request.method == 'POST':
            content = request.form.get('content')
            if content:
                Message.send(current_user.id, user_id, content)
                flash('消息发送成功！')
        
        # 获取对话内容
        messages = Message.get_conversation(current_user.id, user_id)
        other_user = User.get_by_id(user_id)
        
        # 标记消息为已读
        Message.mark_as_read(current_user.id, user_id)
        
        return render_template('social/conversation.html',
                             messages=messages,
                             other_user=other_user)
    except Exception as e:
        print(f"Error in conversation: {str(e)}")
        flash('获取对话失败')
        return redirect(url_for('social.messages'))

@social_bp.route('/api/unread_count')
@login_required
def unread_count():
    try:
        count = Message.get_unread_count(current_user.id)
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        return jsonify({'count': 0}) 