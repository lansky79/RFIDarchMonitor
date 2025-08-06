#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
档案信息和位置追踪数据模型
处理档案基础信息和位置历史记录
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base import BaseModel, ValidationError, validate_required_fields, validate_field_length

logger = logging.getLogger(__name__)

class Archive(BaseModel):
    """档案信息模型"""
    
    table_name = 'archives'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['archive_code', 'title']
    FIELD_LENGTHS = {
        'archive_code': 50,
        'title': 200,
        'category': 100,
        'description': 500,
        'rfid_tag_id': 50,
        'current_location': 100,
        'created_by': 50
    }
    
    # 档案状态常量
    STATUS_NORMAL = 'normal'
    STATUS_BORROWED = 'borrowed'
    STATUS_MISSING = 'missing'
    STATUS_DAMAGED = 'damaged'
    STATUS_ARCHIVED = 'archived'
    
    # 档案分类常量
    CATEGORY_DOCUMENT = '文件档案'
    CATEGORY_PHOTO = '照片档案'
    CATEGORY_VIDEO = '视频档案'
    CATEGORY_AUDIO = '音频档案'
    CATEGORY_ELECTRONIC = '电子档案'
    CATEGORY_OTHER = '其他档案'
    
    def __init__(self, **kwargs):
        """初始化档案信息"""
        # 设置默认值
        if 'status' not in kwargs:
            kwargs['status'] = self.STATUS_NORMAL
        if 'category' not in kwargs:
            kwargs['category'] = self.CATEGORY_DOCUMENT
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'Archive':
        """创建档案记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证字段长度
        validate_field_length(kwargs, cls.FIELD_LENGTHS)
        
        # 验证档案编号唯一性
        if 'archive_code' in kwargs:
            existing = cls.find_one("archive_code = ?", [kwargs['archive_code']])
            if existing:
                raise ValidationError(f"档案编号 '{kwargs['archive_code']}' 已存在")
        
        # 验证RFID标签是否已被使用
        if 'rfid_tag_id' in kwargs and kwargs['rfid_tag_id']:
            existing = cls.find_one("rfid_tag_id = ? AND rfid_tag_id != ''", 
                                  [kwargs['rfid_tag_id']])
            if existing:
                raise ValidationError(f"RFID标签 '{kwargs['rfid_tag_id']}' 已被使用")
        
        return cls.create(**kwargs)
    
    @classmethod
    def find_by_code(cls, archive_code: str) -> Optional['Archive']:
        """根据档案编号查找档案"""
        return cls.find_one("archive_code = ?", [archive_code])
    
    @classmethod
    def find_by_rfid_tag(cls, tag_id: str) -> Optional['Archive']:
        """根据RFID标签ID查找档案"""
        return cls.find_one("rfid_tag_id = ?", [tag_id])
    
    @classmethod
    def get_archives_by_category(cls, category: str) -> List['Archive']:
        """根据分类获取档案列表"""
        return cls.find_all("category = ?", [category], order_by="archive_code ASC")
    
    @classmethod
    def get_archives_by_status(cls, status: str) -> List['Archive']:
        """根据状态获取档案列表"""
        return cls.find_all("status = ?", [status], order_by="archive_code ASC")
    
    @classmethod
    def get_archives_by_location(cls, location: str) -> List['Archive']:
        """根据当前位置获取档案列表"""
        return cls.find_all("current_location = ?", [location], 
                          order_by="archive_code ASC")
    
    @classmethod
    def search_archives(cls, keyword: str, category: str = None, 
                       status: str = None) -> List['Archive']:
        """搜索档案"""
        where_conditions = [
            "(archive_code LIKE ? OR title LIKE ? OR description LIKE ?)"
        ]
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(where_conditions)
        
        return cls.find_all(where_clause, params, order_by="archive_code ASC")
    
    def assign_rfid_tag(self, tag_id: str) -> None:
        """分配RFID标签"""
        # 检查标签是否已被使用
        existing = self.__class__.find_one("rfid_tag_id = ? AND id != ?", 
                                         [tag_id, self.id or 0])
        if existing:
            raise ValidationError(f"RFID标签 '{tag_id}' 已被其他档案使用")
        
        self.rfid_tag_id = tag_id
        self.updated_at = datetime.now().isoformat()
        self.save()
        
        # 更新标签信息
        from .rfid import RfidTag
        tag = RfidTag.find_by_tag_id(tag_id)
        if tag:
            tag.assign_to_archive(self.archive_code)
    
    def remove_rfid_tag(self) -> None:
        """移除RFID标签"""
        if self.rfid_tag_id:
            # 更新标签信息
            from .rfid import RfidTag
            tag = RfidTag.find_by_tag_id(self.rfid_tag_id)
            if tag:
                tag.unassign_from_archive()
            
            self.rfid_tag_id = None
            self.updated_at = datetime.now().isoformat()
            self.save()
    
    def update_location(self, location: str, device_id: int = None, 
                       action_type: str = 'manual') -> None:
        """更新档案位置"""
        old_location = self.current_location
        self.current_location = location
        self.updated_at = datetime.now().isoformat()
        self.save()
        
        # 记录位置历史
        LocationHistory.create(
            archive_id=self.id,
            rfid_device_id=device_id,
            location=location,
            action_type=action_type,
            notes=f"从 '{old_location or '未知'}' 移动到 '{location}'"
        )
        
        logger.info(f"档案 {self.archive_code} 位置更新: {old_location} -> {location}")
    
    def update_status(self, status: str, notes: str = None) -> None:
        """更新档案状态"""
        if status not in [self.STATUS_NORMAL, self.STATUS_BORROWED, 
                         self.STATUS_MISSING, self.STATUS_DAMAGED, self.STATUS_ARCHIVED]:
            raise ValidationError(f"无效的档案状态: {status}")
        
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now().isoformat()
        self.save()
        
        # 记录状态变更历史
        LocationHistory.create(
            archive_id=self.id,
            location=self.current_location or '未知',
            action_type='status_change',
            notes=f"状态从 '{old_status}' 变更为 '{status}'" + (f": {notes}" if notes else "")
        )
        
        logger.info(f"档案 {self.archive_code} 状态更新: {old_status} -> {status}")
    
    def get_location_history(self, limit: int = 50) -> List['LocationHistory']:
        """获取位置历史记录"""
        return LocationHistory.find_all(
            "archive_id = ?", 
            [self.id], 
            order_by="timestamp DESC", 
            limit=limit
        )
    
    def get_current_location_info(self) -> Dict[str, Any]:
        """获取当前位置信息"""
        latest_history = LocationHistory.find_all(
            "archive_id = ?", 
            [self.id], 
            order_by="timestamp DESC", 
            limit=1
        )
        
        if latest_history:
            history = latest_history[0]
            return {
                'location': self.current_location or '未知',
                'last_update': history.timestamp,
                'action_type': history.action_type,
                'device_id': history.rfid_device_id
            }
        else:
            return {
                'location': self.current_location or '未知',
                'last_update': self.updated_at,
                'action_type': 'manual',
                'device_id': None
            }
    
    def is_missing(self) -> bool:
        """检查档案是否丢失"""
        return self.status == self.STATUS_MISSING
    
    def is_available(self) -> bool:
        """检查档案是否可用"""
        return self.status == self.STATUS_NORMAL
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """获取档案统计信息"""
        total_count = cls.count()
        
        # 按状态统计
        status_stats = {}
        for status in [cls.STATUS_NORMAL, cls.STATUS_BORROWED, cls.STATUS_MISSING, 
                      cls.STATUS_DAMAGED, cls.STATUS_ARCHIVED]:
            count = cls.count("status = ?", [status])
            status_stats[status] = count
        
        # 按分类统计
        category_stats = {}
        for category in [cls.CATEGORY_DOCUMENT, cls.CATEGORY_PHOTO, cls.CATEGORY_VIDEO,
                        cls.CATEGORY_AUDIO, cls.CATEGORY_ELECTRONIC, cls.CATEGORY_OTHER]:
            count = cls.count("category = ?", [category])
            category_stats[category] = count
        
        # RFID标签使用统计
        tagged_count = cls.count("rfid_tag_id IS NOT NULL AND rfid_tag_id != ''")
        
        return {
            'total_count': total_count,
            'tagged_count': tagged_count,
            'untagged_count': total_count - tagged_count,
            'status_statistics': status_stats,
            'category_statistics': category_stats
        }


class LocationHistory(BaseModel):
    """位置历史记录模型"""
    
    table_name = 'location_history'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['archive_id', 'location']
    FIELD_LENGTHS = {
        'location': 100,
        'action_type': 50,
        'notes': 200
    }
    
    # 动作类型常量
    ACTION_SCAN = 'scan'
    ACTION_MANUAL = 'manual'
    ACTION_BORROW = 'borrow'
    ACTION_RETURN = 'return'
    ACTION_MOVE = 'move'
    ACTION_STATUS_CHANGE = 'status_change'
    
    def __init__(self, **kwargs):
        """初始化位置历史记录"""
        # 设置默认值
        if 'action_type' not in kwargs:
            kwargs['action_type'] = self.ACTION_SCAN
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now().isoformat()
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'LocationHistory':
        """创建位置历史记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证字段长度
        validate_field_length(kwargs, cls.FIELD_LENGTHS)
        
        # 验证档案ID存在性
        if 'archive_id' in kwargs:
            archive = Archive.find_by_id(kwargs['archive_id'])
            if not archive:
                raise ValidationError(f"档案ID {kwargs['archive_id']} 不存在")
        
        return cls.create(**kwargs)
    
    @classmethod
    def get_archive_history(cls, archive_id: int, limit: int = 50) -> List['LocationHistory']:
        """获取指定档案的位置历史"""
        return cls.find_all(
            "archive_id = ?", 
            [archive_id], 
            order_by="timestamp DESC", 
            limit=limit
        )
    
    @classmethod
    def get_location_activities(cls, location: str, limit: int = 50) -> List['LocationHistory']:
        """获取指定位置的活动记录"""
        return cls.find_all(
            "location = ?", 
            [location], 
            order_by="timestamp DESC", 
            limit=limit
        )
    
    @classmethod
    def get_recent_activities(cls, hours: int = 24, limit: int = 100) -> List['LocationHistory']:
        """获取最近的活动记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return cls.find_all(
            "timestamp >= ?", 
            [cutoff_time.isoformat()], 
            order_by="timestamp DESC", 
            limit=limit
        )
    
    @classmethod
    def get_device_activities(cls, device_id: int, limit: int = 50) -> List['LocationHistory']:
        """获取指定设备的扫描记录"""
        return cls.find_all(
            "rfid_device_id = ?", 
            [device_id], 
            order_by="timestamp DESC", 
            limit=limit
        )
    
    @classmethod
    def get_movement_statistics(cls, start_time: datetime, 
                              end_time: datetime) -> Dict[str, Any]:
        """获取移动统计信息"""
        where_clause = "timestamp BETWEEN ? AND ?"
        params = [start_time.isoformat(), end_time.isoformat()]
        
        # 总活动次数
        total_activities = cls.count(where_clause, params)
        
        # 按动作类型统计
        action_stats = {}
        for action in [cls.ACTION_SCAN, cls.ACTION_MANUAL, cls.ACTION_BORROW,
                      cls.ACTION_RETURN, cls.ACTION_MOVE, cls.ACTION_STATUS_CHANGE]:
            count = cls.count(f"{where_clause} AND action_type = ?", 
                            params + [action])
            action_stats[action] = count
        
        # 按位置统计
        sql = f"""
            SELECT location, COUNT(*) as count
            FROM {cls.table_name}
            WHERE {where_clause}
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        """
        location_stats = cls.execute_raw_sql(sql, params, fetch_one=False, fetch_all=True)
        
        # 按设备统计
        sql = f"""
            SELECT rfid_device_id, COUNT(*) as count
            FROM {cls.table_name}
            WHERE {where_clause} AND rfid_device_id IS NOT NULL
            GROUP BY rfid_device_id
            ORDER BY count DESC
        """
        device_stats = cls.execute_raw_sql(sql, params, fetch_one=False, fetch_all=True)
        
        return {
            'total_activities': total_activities,
            'action_statistics': action_stats,
            'top_locations': location_stats,
            'device_statistics': device_stats
        }
    
    def get_archive_info(self) -> Optional[Dict[str, Any]]:
        """获取关联档案信息"""
        if not self.archive_id:
            return None
        
        archive = Archive.find_by_id(self.archive_id)
        if archive:
            return {
                'archive_code': archive.archive_code,
                'title': archive.title,
                'category': archive.category,
                'status': archive.status
            }
        return None
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """获取关联设备信息"""
        if not self.rfid_device_id:
            return None
        
        from .rfid import RfidDevice
        device = RfidDevice.find_by_id(self.rfid_device_id)
        if device:
            return {
                'device_name': device.device_name,
                'device_type': device.device_type,
                'location': device.location
            }
        return None
    
    def to_json_dict(self) -> Dict[str, Any]:
        """转换为JSON兼容的字典"""
        result = super().to_json_dict()
        
        # 添加关联信息
        result['archive_info'] = self.get_archive_info()
        result['device_info'] = self.get_device_info()
        
        return result
    
    @classmethod
    def cleanup_old_records(cls, days_to_keep: int = 365) -> int:
        """清理旧的位置记录"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 先统计要删除的记录数
        count = cls.count("timestamp < ?", [cutoff_date.isoformat()])
        
        if count > 0:
            sql = f"DELETE FROM {cls.table_name} WHERE timestamp < ?"
            cls.execute_raw_sql(sql, [cutoff_date.isoformat()], 
                              fetch_one=False, fetch_all=False)
            logger.info(f"清理了 {count} 条位置历史记录")
        
        return count