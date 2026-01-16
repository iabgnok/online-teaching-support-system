from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    db, GradeCategory, GradeItem, StudentGradeScore, StudentFinalGrade,
    TeacherClass, StudentClass, Assignment, Submission, Attendance, AttendanceRecord,
    TeachingClass, Student,
    generate_next_id
)
from datetime import datetime
from sqlalchemy import func

grades_bp = Blueprint('grades', __name__, url_prefix='/api/v1/grades')


# ==================== 成绩分类管理 ====================

@grades_bp.route('/class/<int:class_id>/categories', methods=['GET'])
@login_required
def get_grade_categories(class_id):
    """获取班级的成绩分类配置"""
    categories = GradeCategory.query.filter_by(class_id=class_id).order_by(GradeCategory.order).all()
    
    result = []
    for cat in categories:
        items = GradeItem.query.filter_by(category_id=cat.id).all()
        result.append({
            'id': cat.id,
            'name': cat.name,
            'weight': float(cat.weight) if cat.weight else 0,
            'description': cat.description,
            'order': cat.order,
            'items': [{
                'id': item.id,
                'name': item.name,
                'type': item.item_type,
                'weight': float(item.weight) if item.weight else 0,
                'max_score': float(item.max_score) if item.max_score else 100,
                'auto_calculate': item.auto_calculate,
                'is_published': item.is_published
            } for item in items]
        })
    
    return jsonify(result)


@grades_bp.route('/class/<int:class_id>/categories', methods=['POST'])
@login_required
def create_grade_category(class_id):
    """创建成绩分类"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    category = GradeCategory(
        id=generate_next_id(GradeCategory),
        class_id=class_id,
        name=data.get('name'),
        weight=data.get('weight', 0),
        description=data.get('description', ''),
        order=data.get('order', 0)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'message': 'Created', 'id': category.id}), 201


@grades_bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_grade_category(category_id):
    """更新成绩分类"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    category = GradeCategory.query.get_or_404(category_id)
    data = request.json
    
    if 'name' in data:
        category.name = data['name']
    if 'weight' in data:
        category.weight = data['weight']
    if 'description' in data:
        category.description = data['description']
    if 'order' in data:
        category.order = data['order']
    
    db.session.commit()
    return jsonify({'message': 'Updated'})


@grades_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_grade_category(category_id):
    """删除成绩分类"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    category = GradeCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Deleted'})


# ==================== 成绩项管理 ====================

@grades_bp.route('/categories/<int:category_id>/items', methods=['POST'])
@login_required
def create_grade_item(category_id):
    """创建成绩项"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    category = GradeCategory.query.get_or_404(category_id)
    data = request.json
    
    item = GradeItem(
        id=generate_next_id(GradeItem),
        category_id=category_id,
        class_id=category.class_id,
        name=data.get('name'),
        item_type=data.get('type', 'manual'),
        weight=data.get('weight'),
        max_score=data.get('max_score', 100),
        related_assignment_id=data.get('related_assignment_id'),
        auto_calculate=data.get('auto_calculate', False),
        is_published=data.get('is_published', False),
        created_by=current_user.teacher_profile.teacher_id if current_user.teacher_profile else None
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({'message': 'Created', 'id': item.id}), 201


@grades_bp.route('/items/<int:item_id>', methods=['PUT'])
@login_required
def update_grade_item(item_id):
    """更新成绩项"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = GradeItem.query.get_or_404(item_id)
    data = request.json
    
    for field in ['name', 'weight', 'max_score', 'is_published']:
        if field in data:
            setattr(item, field, data[field])
    
    db.session.commit()
    return jsonify({'message': 'Updated'})


@grades_bp.route('/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_grade_item(item_id):
    """删除成绩项"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = GradeItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Deleted'})


# ==================== 成绩录入与查询 ====================

@grades_bp.route('/items/<int:item_id>/scores', methods=['GET'])
@login_required
def get_item_scores(item_id):
    """获取某成绩项的所有学生得分"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = GradeItem.query.get_or_404(item_id)
    
    # 获取班级所有学生
    students = StudentClass.query.filter_by(class_id=item.class_id, status=1).all()
    
    result = []
    for enrollment in students:
        student = enrollment.student
        score_record = StudentGradeScore.query.filter_by(
            grade_item_id=item_id,
            student_id=student.student_id
        ).first()
        
        result.append({
            'student_id': student.student_id,
            'student_no': student.student_no,
            'name': student.user.real_name,
            'score': float(score_record.score) if score_record and score_record.score else None,
            'percentage': float(score_record.percentage) if score_record and score_record.percentage else None,
            'remarks': score_record.remarks if score_record else None
        })
    
    return jsonify(result)


@grades_bp.route('/items/<int:item_id>/scores', methods=['POST'])
@login_required
def batch_update_scores(item_id):
    """批量更新成绩"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = GradeItem.query.get_or_404(item_id)
    data = request.json.get('scores', [])
    
    teacher_id = current_user.teacher_profile.teacher_id if current_user.teacher_profile else None
    
    for score_data in data:
        student_id = score_data.get('student_id')
        score_value = score_data.get('score')
        
        if score_value is None:
            continue
        
        # 计算百分制得分
        percentage = (float(score_value) / float(item.max_score)) * 100 if item.max_score else 0
        
        # 查找或创建成绩记录
        score_record = StudentGradeScore.query.filter_by(
            grade_item_id=item_id,
            student_id=student_id
        ).first()
        
        if score_record:
            score_record.score = score_value
            score_record.percentage = percentage
            score_record.graded_by = teacher_id
            score_record.graded_at = datetime.now()
        else:
            score_record = StudentGradeScore(
                id=generate_next_id(StudentGradeScore),
                grade_item_id=item_id,
                student_id=student_id,
                class_id=item.class_id,
                score=score_value,
                percentage=percentage,
                graded_by=teacher_id,
                graded_at=datetime.now()
            )
            db.session.add(score_record)
    
    db.session.commit()
    return jsonify({'message': 'Scores updated successfully'})


# ==================== 自动计算考勤成绩 ====================

@grades_bp.route('/items/<int:item_id>/calculate-attendance', methods=['POST'])
@login_required
def calculate_attendance_score(item_id):
    """自动计算考勤成绩"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    item = GradeItem.query.get_or_404(item_id)
    
    if item.item_type != 'attendance':
        return jsonify({'error': 'This is not an attendance item'}), 400
    
    # 获取班级所有考勤记录
    attendances = Attendance.query.filter_by(class_id=item.class_id).all()
    total_sessions = len(attendances)
    
    if total_sessions == 0:
        return jsonify({'error': 'No attendance records found'}), 400
    
    # 获取班级所有学生
    students = StudentClass.query.filter_by(class_id=item.class_id, status=1).all()
    
    teacher_id = current_user.teacher_profile.teacher_id if current_user.teacher_profile else None
    
    for enrollment in students:
        student_id = enrollment.student_id
        
        # 统计出勤情况
        present_count = 0
        late_count = 0
        
        for attendance in attendances:
            record = AttendanceRecord.query.filter_by(
                attendance_id=attendance.id,
                student_id=student_id
            ).first()
            
            if record:
                if record.status == 'present':
                    present_count += 1
                elif record.status == 'late':
                    late_count += 1
        
        # 计算考勤分：出勤得1分，迟到得0.8分，缺勤得0分
        attendance_score = (present_count + late_count * 0.8) / total_sessions * 100
        
        # 更新或创建成绩记录
        score_record = StudentGradeScore.query.filter_by(
            grade_item_id=item_id,
            student_id=student_id
        ).first()
        
        if score_record:
            score_record.score = attendance_score
            score_record.percentage = attendance_score
            score_record.graded_by = teacher_id
            score_record.graded_at = datetime.now()
        else:
            score_record = StudentGradeScore(
                id=generate_next_id(StudentGradeScore),
                grade_item_id=item_id,
                student_id=student_id,
                class_id=item.class_id,
                score=attendance_score,
                percentage=attendance_score,
                graded_by=teacher_id,
                graded_at=datetime.now()
            )
            db.session.add(score_record)
    
    db.session.commit()
    return jsonify({'message': 'Attendance scores calculated', 'total_sessions': total_sessions})


# ==================== 总评成绩计算 ====================

@grades_bp.route('/class/<int:class_id>/calculate-final', methods=['POST'])
@login_required
def calculate_final_grades(class_id):
    """计算班级总评成绩和排名"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取所有分类
    categories = GradeCategory.query.filter_by(class_id=class_id).all()
    
    if not categories:
        return jsonify({'error': 'No grade categories configured'}), 400
    
    # 获取班级所有学生
    students = StudentClass.query.filter_by(class_id=class_id, status=1).all()
    
    student_scores = []
    
    for enrollment in students:
        student_id = enrollment.student_id
        category_scores_dict = {}
        total_score = 0
        
        for category in categories:
            # 获取该分类下的所有成绩项
            items = GradeItem.query.filter_by(category_id=category.id).all()
            
            if not items:
                continue
            
            # 计算分类得分（各项加权平均）
            category_total = 0
            category_weight_sum = 0
            
            for item in items:
                score_record = StudentGradeScore.query.filter_by(
                    grade_item_id=item.id,
                    student_id=student_id
                ).first()
                
                if score_record and score_record.percentage is not None:
                    item_weight = float(item.weight) if item.weight else 1
                    category_total += float(score_record.percentage) * item_weight
                    category_weight_sum += item_weight
            
            # 分类得分（百分制）
            category_score = category_total / category_weight_sum if category_weight_sum > 0 else 0
            category_scores_dict[category.name] = round(category_score, 2)
            
            # 累加到总分
            category_weight = float(category.weight) if category.weight else 0
            total_score += category_score * (category_weight / 100)
        
        student_scores.append({
            'student_id': student_id,
            'total_score': round(total_score, 2),
            'category_scores': category_scores_dict
        })
    
    # 排序计算排名
    student_scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    for rank, score_data in enumerate(student_scores, 1):
        student_id = score_data['student_id']
        total_score = score_data['total_score']
        category_scores = score_data['category_scores']
        
        # 更新或创建总评记录
        final_grade = StudentFinalGrade.query.filter_by(
            student_id=student_id,
            class_id=class_id
        ).first()
        
        if final_grade:
            final_grade.total_score = total_score
            final_grade.rank = rank
            final_grade.rank_percentage = round((rank / len(student_scores)) * 100, 2)
            final_grade.category_scores = category_scores
            final_grade.calculated_at = datetime.now()
        else:
            final_grade = StudentFinalGrade(
                id=generate_next_id(StudentFinalGrade),
                student_id=student_id,
                class_id=class_id,
                total_score=total_score,
                rank=rank,
                rank_percentage=round((rank / len(student_scores)) * 100, 2),
                category_scores=category_scores,
                calculated_at=datetime.now()
            )
            db.session.add(final_grade)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Final grades calculated',
        'total_students': len(student_scores)
    })


# ==================== 学生查看成绩 ====================

@grades_bp.route('/student/class/<int:class_id>/my-grades', methods=['GET'])
@login_required
def get_my_grades(class_id):
    """学生查看自己的成绩"""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = current_user.student_profile
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # 获取成绩配置
    categories = GradeCategory.query.filter_by(class_id=class_id).order_by(GradeCategory.order).all()
    
    result = {
        'categories': [],
        'final_grade': None
    }
    
    for category in categories:
        items = GradeItem.query.filter_by(category_id=category.id, is_published=True).all()
        
        category_data = {
            'name': category.name,
            'weight': float(category.weight) if category.weight else 0,
            'items': []
        }
        
        for item in items:
            score_record = StudentGradeScore.query.filter_by(
                grade_item_id=item.id,
                student_id=student.student_id
            ).first()
            
            category_data['items'].append({
                'name': item.name,
                'max_score': float(item.max_score) if item.max_score else 100,
                'score': float(score_record.score) if score_record and score_record.score else None,
                'percentage': float(score_record.percentage) if score_record and score_record.percentage else None
            })
        
        result['categories'].append(category_data)
    
    # 获取总评成绩
    final_grade = StudentFinalGrade.query.filter_by(
        student_id=student.student_id,
        class_id=class_id,
        is_published=True
    ).first()
    
    if final_grade:
        result['final_grade'] = {
            'total_score': float(final_grade.total_score) if final_grade.total_score else None,
            'rank': final_grade.rank,
            'rank_percentage': float(final_grade.rank_percentage) if final_grade.rank_percentage else None,
            'category_scores': final_grade.category_scores
        }
    
    return jsonify(result)


# ==================== 成绩统计 ====================

@grades_bp.route('/class/<int:class_id>/statistics', methods=['GET'])
@login_required
def get_grade_statistics(class_id):
    """获取成绩统计信息"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 先检查是否配置了成绩结构
    categories = GradeCategory.query.filter_by(class_id=class_id).all()
    has_config = len(categories) > 0
    
    final_grades = StudentFinalGrade.query.filter_by(class_id=class_id).order_by(StudentFinalGrade.rank).all()
    
    if not final_grades:
        # 返回空统计数据，但标记是否有配置
        return jsonify({
            'total_students': 0,
            'average': 0,
            'highest': 0,
            'lowest': 0,
            'pass_rate': 0,
            'excellent_rate': 0,
            'distribution': {},
            'rankings': [],
            'has_data': False,
            'has_config': has_config,
            'message': '请先录入成绩并计算总评' if has_config else '请先配置成绩结构'
        })
    
    scores = [float(g.total_score) for g in final_grades if g.total_score]
    
    if not scores:
        return jsonify({
            'total_students': 0,
            'average': 0,
            'highest': 0,
            'lowest': 0,
            'pass_rate': 0,
            'excellent_rate': 0,
            'distribution': {},
            'rankings': [],
            'has_data': False,
            'has_config': has_config,
            'message': '请先录入成绩并计算总评' if has_config else '请先配置成绩结构'
        })
    
    # 基本统计
    stats = {
        'total_students': len(scores),
        'average': round(sum(scores) / len(scores), 2),
        'highest': max(scores),
        'lowest': min(scores),
        'pass_rate': round(len([s for s in scores if s >= 60]) / len(scores) * 100, 2),
        'excellent_rate': round(len([s for s in scores if s >= 85]) / len(scores) * 100, 2),
        'has_data': True
    }
    
    # 分数段分布
    score_distribution = {
        '90-100': len([s for s in scores if 90 <= s <= 100]),
        '80-89': len([s for s in scores if 80 <= s < 90]),
        '70-79': len([s for s in scores if 70 <= s < 80]),
        '60-69': len([s for s in scores if 60 <= s < 70]),
        '0-59': len([s for s in scores if s < 60])
    }
    
    stats['distribution'] = score_distribution
    
    # 排名数据
    rankings = []
    for grade in final_grades:
        from models import Student, Users
        student = Student.query.get(grade.student_id)
        if student:
            user = Users.query.get(student.user_id)
            rankings.append({
                'rank': grade.rank,
                'student_no': student.student_no,
                'name': user.real_name if user else '未知',
                'total_score': float(grade.total_score) if grade.total_score else 0,
                'category_scores': grade.category_scores or {}
            })
    
    stats['rankings'] = rankings
    
    return jsonify(stats)


# ==================== 新增API：前端所需的接口 ====================

@grades_bp.route('/class/<int:class_id>/items', methods=['GET'])
@login_required
def get_all_grade_items(class_id):
    """获取班级的所有成绩项（不包括作业和考试）"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取所有成绩项（排除关联到作业的）
    categories = GradeCategory.query.filter_by(class_id=class_id).all()
    
    result = []
    for category in categories:
        items = GradeItem.query.filter_by(category_id=category.id).all()
        for item in items:
            # 只返回非作业类型的成绩项
            if item.item_type in ['attendance', 'participation', 'project', 'other']:
                result.append({
                    'id': item.id,
                    'name': item.name,
                    'type': item.item_type,
                    'max_score': float(item.max_score) if item.max_score else 100,
                    'category_name': category.name,
                    'weight': float(item.weight) if item.weight else 0
                })
    
    return jsonify(result)


@grades_bp.route('/class/<int:class_id>/final', methods=['GET'])
@login_required
def get_final_grades(class_id):
    """获取班级的总成绩列表"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # 获取成绩分类
    categories = GradeCategory.query.filter_by(class_id=class_id).order_by(GradeCategory.order).all()
    
    # 获取所有学生的总成绩
    final_grades = StudentFinalGrade.query.filter_by(class_id=class_id).order_by(StudentFinalGrade.rank).all()
    
    def calculate_grade_level(score):
        """根据分数计算等级"""
        if score is None:
            return None
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def calculate_category_scores(student_id, categories):
        """计算学生各分类的得分"""
        category_scores = {}
        for category in categories:
            items = GradeItem.query.filter_by(category_id=category.id).all()
            if not items:
                continue
            
            total_weight = sum(float(item.weight or 0) for item in items)
            if total_weight == 0:
                continue
            
            category_score = 0
            for item in items:
                score_record = StudentGradeScore.query.filter_by(
                    grade_item_id=item.id,
                    student_id=student_id
                ).first()
                
                if score_record and score_record.score is not None:
                    item_weight = float(item.weight or 0)
                    item_percentage = (float(score_record.score) / float(item.max_score)) * 100 if item.max_score else 0
                    category_score += (item_percentage * item_weight / total_weight)
            
            category_scores[category.id] = round(category_score, 2)
        
        return category_scores
    
    students_data = []
    for grade in final_grades:
        from models import Student, Users
        student = Student.query.get(grade.student_id)
        if not student:
            continue
        
        user = Users.query.get(student.user_id)
        
        # 动态计算各分类成绩
        category_scores = calculate_category_scores(student.student_id, categories)
        
        final_score = float(grade.total_score) if grade.total_score else None
        
        students_data.append({
            'student_id': student.student_id,
            'student_no': student.student_no,
            'student_name': user.real_name if user else '未知',
            'final_score': final_score,
            'grade_level': calculate_grade_level(final_score),
            'rank': grade.rank,
            'category_scores': category_scores
        })
    
    # 如果没有总成绩记录，返回学生列表但成绩为空
    if not students_data:
        enrollments = StudentClass.query.filter_by(class_id=class_id, status=1).all()
        for enrollment in enrollments:
            student = enrollment.student
            user = Users.query.get(student.user_id)
            
            # 也计算分类成绩
            category_scores = calculate_category_scores(student.student_id, categories)
            
            students_data.append({
                'student_id': student.student_id,
                'student_no': student.student_no,
                'student_name': user.real_name if user else '未知',
                'final_score': None,
                'grade_level': None,
                'rank': None,
                'category_scores': category_scores
            })
    
    return jsonify({
        'students': students_data,
        'categories': [{
            'id': cat.id,
            'name': cat.name,
            'weight': float(cat.weight) if cat.weight else 0
        } for cat in categories]
    })


@grades_bp.route('/item/<int:item_id>/score', methods=['POST'])
@login_required
def update_single_score(item_id):
    """更新单个学生的成绩"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    student_id = data.get('student_id')
    score = data.get('score')
    
    if not student_id or score is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    item = GradeItem.query.get_or_404(item_id)
    
    # 查找或创建成绩记录
    score_record = StudentGradeScore.query.filter_by(
        grade_item_id=item_id,
        student_id=student_id
    ).first()
    
    if not score_record:
        score_record = StudentGradeScore(
            id=generate_next_id(StudentGradeScore),
            grade_item_id=item_id,
            student_id=student_id
        )
        db.session.add(score_record)
    
    score_record.score = float(score)
    score_record.percentage = (float(score) / float(item.max_score)) * 100 if item.max_score else 0
    score_record.graded_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({'message': 'Score updated successfully'})

@grades_bp.route('/class/<int:class_id>/student/<int:student_id>/scores', methods=['GET'])
@login_required
def get_student_all_scores(class_id, student_id):
    """获取指定学生在某个班级的所有成绩项得分"""
    try:
        if current_user.role not in ['teacher', 'admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # 获取班级和学生信息
        class_info = TeachingClass.query.get(class_id)
        if not class_info:
            return jsonify({'error': 'Class not found'}), 404
        
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # 获取该班级所有分类下的成绩项
        categories = GradeCategory.query.filter_by(class_id=class_id).all()
        
        all_scores = []
        for category in categories:
            items = GradeItem.query.filter_by(category_id=category.id).all()
            for item in items:
                score_record = StudentGradeScore.query.filter_by(
                    grade_item_id=item.id,
                    student_id=student_id
                ).first()
                
                all_scores.append({
                    'grade_item_id': item.id,
                    'item_name': item.name,
                    'category_id': category.id,
                    'category_name': category.name,
                    'max_score': float(item.max_score) if item.max_score else 0,
                    'weight': float(item.weight) if item.weight else 0,
                    'score': float(score_record.score) if score_record and score_record.score is not None else None
                })
        
        return jsonify(all_scores)
    except Exception as e:
        print(f"Error in get_student_all_scores: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
