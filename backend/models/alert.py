#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理数据模型
处理系统告警信息的存储和管理
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base import BaseModel, ValidationError, validate_required_fields, validate_field_length

logger = logging.getLogger(__name__)

class Alert(BaseModel):
    """告警信息模型"""
    
    table_name = 'alerts'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['alert_type', 'level', 'title', 'message']
    FIELD_LENGTHS = {
        'alert_type': 50,
        'level': 20,
        'title': 200,
        'message': 500,
        'source_id': 50,
        'source_type': 50,
        'handled_by': 50
    }
    
    # 告警类型常量
    TYPE_ENVIRONMENT = 'environment'
    TYPE_MOVEMENT = 'movement'
    TYPE_SYSTEM = 'system'
    TYPE_DEVICE = 'device'
    TYPE_INVENTORY = 'inventory'
    
    # 告警级别常量
    LEVEL_INFO = 'info'
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVEL_CRITICAL = 'critical'
    
    # 告警状态常量
    STATUS_PENDING = 'pending'
    STATUS_HANDLED = 'handled'
    STATUS_IGNORED = 'ignored'
    STATUS_RESOLVED = 'resolved'
    
    def __init__(self, **kwargs):
        """初始化告警信息"""
        # 设置默认值
        if 'status' not in kwargs:
            kwargs['status'] = self.STATUS_PENDING
        if 'level' not in kwargs:
            kwargs['level'] = self.LEVEL_WARNING
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'Alert':
        """创建告警记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证字段长度
        validate_field_length(kwargs, cls.FIELD_LENGTHS)
        
        # 验证告警类型
        if 'alert_type' in kwargs:
            valid_types = [cls.TYPE_ENVIRONMENT, cls.TYPE_MOVEMENT, cls.TYPE_SYSTEM,
                          cls.TYPE_DEVICE, cls.TYPE_INVENTORY]
            if kwargs['alert_type'] not in valid_types:
                raise ValidationError(f"无效的告警类型: {kwargs['alert_type']}")
        
        # 验证告警级别
        if 'level' in kwargs:
            valid_levels = [cls.LEVEL_INFO, cls.LEVEL_WARNING, cls.LEVEL_ERROR, cls.LEVEL_CRITICAL]
            if kwargs['level'] not in valid_levels:
                raise ValidationError(f"无效的告警级别: {kwargs['level']}")
        
        return cls.create(**kwargs)
    
    @classmethod
    def get_pending_alerts(cls, limit: int = 50) -> List['Alert']:
        """获取待处理告警"""
        return cls.find_all("status = ?", [cls.STATUS_PENDING], 
                          order_by="created_at DESC", limit=limit)
    
    @classmethod
    def get_alerts_by_type(cls, alert_type: str, limit: int = 50) -> List['Alert']:
        """根据类型获取告警"""
        return cls.find_all("alert_type = ?", [alert_type], 
                          order_by="created_at DESC", limit=limit)
    
    @classmethod
    def get_alerts_by_level(cls, level: str, limit: int = 50) -> List['Alert']:
        """根据级别获取告警"""
        return cls.find_all("level = ?", [level], 
                          order_by="created_at DESC", limit=limit)
    
    @classmethod
    def get_recent_alerts(cls, hours: int = 24, limit: int = 100) -> List['Alert']:
        """获取最近的告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return cls.find_all("created_at >= ?", [cutoff_time.isoformat()], 
                          order_by="created_at DESC", limit=limit)
    
    def handle_alert(self, handled_by: str, notes: str = None) -> None:
        """处理告警"""
        self.status = self.STATUS_HANDLED
        self.handled_by = handled_by
        self.handled_at = datetime.now().isoformat()
        
        if notes:
            self.message += f"\n处理备注: {notes}"
        
        self.save()
        logger.info(f"告警已处理: ID={self.id}, 处理人={handled_by}")
    
    def ignore_alert(self, handled_by: str, reason: str = None) -> None:
        """忽略告警"""
        self.status = self.STATUS_IGNORED
        self.handled_by = handled_by
        self.handled_at = datetime.now().isoformat()
        
        if reason:
            self.message += f"\n忽略原因: {reason}"
        
        self.save()
        logger.info(f"告警已忽略: ID={self.id}, 处理人={handled_by}")
    
    def resolve_alert(self, handled_by: str, solution: str = None) -> None:
        """解决告警"""
        self.status = self.STATUS_RESOLVED
        self.handled_by = handled_by
        self.handled_at = datetime.now().isoformat()
        
        if solution:
            self.message += f"\n解决方案: {solution}"
        
        self.save()
        logger.info(f"告警已解决: ID={self.id}, 处理人={handled_by}")
    
    def is_pending(self) -> bool:
        """检查告警是否待处理"""
        return self.status == self.STATUS_PENDING
    
    def is_critical(self) -> bool:
        """检查告警是否为严重级别"""
        return self.level == self.LEVEL_CRITICAL
    
    def get_age_hours(self) -> float:
        """获取告警存在时长（小时）"""
        try:
            created_time = datetime.fromisoformat(self.created_at)
            delta = datetime.now() - created_time
            return delta.total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0
    
    @classmethod
    def get_statistics(cls, days: int = 7) -> Dict[str, Any]:
        """获取告警统计信息"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 总告警数
        total_count = cls.count("created_at >= ?", [cutoff_date.isoformat()])
        
        # 待处理告警数
        pending_count = cls.count("status = ? AND created_at >= ?", 
                                [cls.STATUS_PENDING, cutoff_date.isoformat()])
        
        # 按类型统计
        type_stats = {}
        for alert_type in [cls.TYPE_ENVIRONMENT, cls.TYPE_MOVEMENT, cls.TYPE_SYSTEM,
                          cls.TYPE_DEVICE, cls.TYPE_INVENTORY]:
            count = cls.count("alert_type = ? AND created_at >= ?", 
                            [alert_type, cutoff_date.isoformat()])
            type_stats[alert_type] = count
        
        # 按级别统计
        level_stats = {}
        for level in [cls.LEVEL_INFO, cls.LEVEL_WARNING, cls.LEVEL_ERROR, cls.LEVEL_CRITICAL]:
            count = cls.count("level = ? AND created_at >= ?", 
                            [level, cutoff_date.isoformat()])
            level_stats[level] = count
        
        # 按状态统计
        status_stats = {}
        for status in [cls.STATUS_PENDING, cls.STATUS_HANDLED, cls.STATUS_IGNORED, cls.STATUS_RESOLVED]:
            count = cls.count("status = ? AND created_at >= ?", 
                            [status, cutoff_date.isoformat()])
            status_stats[status] = count
        
        return {
            'total_count': total_count,
            'pending_count': pending_count,
            'type_statistics': type_stats,
            'level_statistics': level_stats,
            'status_statistics': status_stats,
            'days': days
        }
    
    @classmethod
    def cleanup_old_alerts(cls, days_to_keep: int = 90) -> int:
        """清理旧告警记录"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 只清理已处理的告警
        where_clause = "created_at < ? AND status IN (?, ?, ?)"
        params = [cutoff_date.isoformat(), cls.STATUS_HANDLED, 
                 cls.STATUS_IGNORED, cls.STATUS_RESOLVED]
        
        # 先统计要删除的记录数
        count = cls.count(where_clause, params)
        
        if count > 0:
            sql = f"DELETE FROM {cls.table_name} WHERE {where_clause}"
            cls.execute_raw_sql(sql, params, fetch_one=False, fetch_all=False)
            logger.info(f"清理了 {count} 条告警记录")
        
        return count
    
    def to_json_dict(self) -> Dict[str, Any]:
        """转换为JSON兼容的字典"""
        result = super().to_json_dict()
        
        # 添加计算字段
        result['age_hours'] = self.get_age_hours()
        result['is_pending'] = self.is_pending()
        result['is_critical'] = self.is_critical()
        
        return result