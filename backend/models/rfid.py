#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID设备和标签数据模型
处理RFID设备配置和标签信息管理
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base import BaseModel, ValidationError, validate_required_fields, validate_field_length

logger = logging.getLogger(__name__)

class RfidDevice(BaseModel):
    """RFID设备模型"""
    
    table_name = 'rfid_devices'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['device_name', 'device_type']
    FIELD_LENGTHS = {
        'device_name': 100,
        'device_type': 50,
        'serial_port': 50,
        'ip_address': 50,
        'location': 100
    }
    
    # 设备状态常量
    STATUS_ONLINE = 'online'
    STATUS_OFFLINE = 'offline'
    STATUS_ERROR = 'error'
    STATUS_MAINTENANCE = 'maintenance'
    
    # 设备类型常量
    TYPE_SERIAL = 'serial'
    TYPE_NETWORK = 'network'
    TYPE_USB = 'usb'
    
    def __init__(self, **kwargs):
        """初始化RFID设备"""
        # 设置默认值
        if 'status' not in kwargs:
            kwargs['status'] = self.STATUS_OFFLINE
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'RfidDevice':
        """创建RFID设备记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证字段长度
        validate_field_length(kwargs, cls.FIELD_LENGTHS)
        
        # 验证设备名称唯一性
        if 'device_name' in kwargs:
            existing = cls.find_one("device_name = ?", [kwargs['device_name']])
            if existing:
                raise ValidationError(f"设备名称 '{kwargs['device_name']}' 已存在")
        
        # 验证IP地址格式（如果是网络设备）
        if kwargs.get('device_type') == cls.TYPE_NETWORK and 'ip_address' in kwargs:
            if not cls._validate_ip_address(kwargs['ip_address']):
                raise ValidationError("IP地址格式不正确")
        
        return cls.create(**kwargs)
    
    @staticmethod
    def _validate_ip_address(ip: str) -> bool:
        """验证IP地址格式"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    @classmethod
    def get_online_devices(cls) -> List['RfidDevice']:
        """获取在线设备列表"""
        return cls.find_all("status = ?", [cls.STATUS_ONLINE], order_by="device_name ASC")
    
    @classmethod
    def get_devices_by_type(cls, device_type: str) -> List['RfidDevice']:
        """根据设备类型获取设备列表"""
        return cls.find_all("device_type = ?", [device_type], order_by="device_name ASC")
    
    @classmethod
    def get_devices_by_location(cls, location: str) -> List['RfidDevice']:
        """根据位置获取设备列表"""
        return cls.find_all("location = ?", [location], order_by="device_name ASC")
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置设备配置"""
        self.config_json = json.dumps(config, ensure_ascii=False)
        self.updated_at = datetime.now().isoformat()
    
    def get_config(self) -> Dict[str, Any]:
        """获取设备配置"""
        if not self.config_json:
            return {}
        try:
            return json.loads(self.config_json)
        except json.JSONDecodeError:
            logger.error(f"设备 {self.device_name} 配置JSON解析失败")
            return {}
    
    def update_status(self, status: str, save: bool = True) -> None:
        """更新设备状态"""
        if status not in [self.STATUS_ONLINE, self.STATUS_OFFLINE, 
                         self.STATUS_ERROR, self.STATUS_MAINTENANCE]:
            raise ValidationError(f"无效的设备状态: {status}")
        
        self.status = status
        self.updated_at = datetime.now().isoformat()
        
        if save:
            self.save()
    
    def is_online(self) -> bool:
        """检查设备是否在线"""
        return self.status == self.STATUS_ONLINE
    
    def get_connection_info(self) -> Dict[str, str]:
        """获取连接信息"""
        if self.device_type == self.TYPE_SERIAL:
            return {'type': 'serial', 'port': self.serial_port or ''}
        elif self.device_type == self.TYPE_NETWORK:
            return {'type': 'network', 'ip': self.ip_address or ''}
        elif self.device_type == self.TYPE_USB:
            return {'type': 'usb', 'port': self.serial_port or ''}
        else:
            return {'type': 'unknown'}


class RfidTag(BaseModel):
    """RFID标签模型"""
    
    table_name = 'rfid_tags'
    primary_key = 'id'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['tag_id']
    FIELD_LENGTHS = {
        'tag_id': 50,
        'archive_id': 50,
        'tag_type': 50,
        'last_seen_location': 100
    }
    
    # 标签状态常量
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_LOST = 'lost'
    STATUS_DAMAGED = 'damaged'
    
    # 标签类型常量
    TYPE_ARCHIVE = '档案标签'
    TYPE_LOCATION = '位置标签'
    TYPE_EQUIPMENT = '设备标签'
    
    def __init__(self, **kwargs):
        """初始化RFID标签"""
        # 设置默认值
        if 'status' not in kwargs:
            kwargs['status'] = self.STATUS_ACTIVE
        if 'tag_type' not in kwargs:
            kwargs['tag_type'] = self.TYPE_ARCHIVE
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'RfidTag':
        """创建RFID标签记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证字段长度
        validate_field_length(kwargs, cls.FIELD_LENGTHS)
        
        # 验证标签ID唯一性
        if 'tag_id' in kwargs:
            existing = cls.find_one("tag_id = ?", [kwargs['tag_id']])
            if existing:
                raise ValidationError(f"标签ID '{kwargs['tag_id']}' 已存在")
        
        # 验证标签ID格式（简单的十六进制检查）
        if 'tag_id' in kwargs:
            tag_id = kwargs['tag_id'].strip().upper()
            if not all(c in '0123456789ABCDEF' for c in tag_id):
                raise ValidationError("标签ID必须是十六进制格式")
            kwargs['tag_id'] = tag_id
        
        return cls.create(**kwargs)
    
    @classmethod
    def find_by_tag_id(cls, tag_id: str) -> Optional['RfidTag']:
        """根据标签ID查找标签"""
        return cls.find_one("tag_id = ?", [tag_id.upper()])
    
    @classmethod
    def get_active_tags(cls) -> List['RfidTag']:
        """获取活跃标签列表"""
        return cls.find_all("status = ?", [cls.STATUS_ACTIVE], order_by="tag_id ASC")
    
    @classmethod
    def get_tags_by_type(cls, tag_type: str) -> List['RfidTag']:
        """根据标签类型获取标签列表"""
        return cls.find_all("tag_type = ?", [tag_type], order_by="tag_id ASC")
    
    @classmethod
    def get_unassigned_tags(cls) -> List['RfidTag']:
        """获取未分配的标签列表"""
        return cls.find_all("archive_id IS NULL OR archive_id = ''", 
                          order_by="tag_id ASC")
    
    @classmethod
    def get_tags_by_location(cls, location: str) -> List['RfidTag']:
        """根据最后见到位置获取标签列表"""
        return cls.find_all("last_seen_location = ?", [location], 
                          order_by="last_seen_time DESC")
    
    @classmethod
    def batch_import_tags(cls, tag_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量导入标签"""
        success_count = 0
        error_count = 0
        errors = []
        
        for i, tag_data in enumerate(tag_data_list):
            try:
                cls.create_with_validation(**tag_data)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"第{i+1}行: {str(e)}")
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors,
            'total_count': len(tag_data_list)
        }
    
    @classmethod
    def export_tags_data(cls, tag_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        """导出标签数据"""
        where_conditions = []
        params = []
        
        if tag_type:
            where_conditions.append("tag_type = ?")
            params.append(tag_type)
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else None
        
        tags = cls.find_all(where_clause, params, order_by="tag_id ASC")
        return [tag.to_json_dict() for tag in tags]
    
    def assign_to_archive(self, archive_id: str) -> None:
        """分配标签给档案"""
        self.archive_id = archive_id
        self.updated_at = datetime.now().isoformat()
        self.save()
    
    def unassign_from_archive(self) -> None:
        """取消标签与档案的关联"""
        self.archive_id = None
        self.updated_at = datetime.now().isoformat()
        self.save()
    
    def update_location(self, location: str, device_id: int = None) -> None:
        """更新标签位置"""
        self.last_seen_location = location
        self.last_seen_time = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.save()
        
        # 记录位置历史（如果有关联的档案）
        if self.archive_id:
            from .archive import LocationHistory
            try:
                LocationHistory.create(
                    archive_id=self._get_archive_id_by_tag(),
                    rfid_device_id=device_id,
                    location=location,
                    action_type='scan'
                )
            except Exception as e:
                # 忽略位置历史记录错误，不影响主要功能
                pass
    
    def _get_archive_id_by_tag(self) -> Optional[int]:
        """根据标签获取档案ID"""
        if not self.archive_id:
            return None
        
        from .archive import Archive
        archive = Archive.find_one("archive_code = ?", [self.archive_id])
        return archive.id if archive else None
    
    def update_status(self, status: str, save: bool = True) -> None:
        """更新标签状态"""
        if status not in [self.STATUS_ACTIVE, self.STATUS_INACTIVE, 
                         self.STATUS_LOST, self.STATUS_DAMAGED]:
            raise ValidationError(f"无效的标签状态: {status}")
        
        self.status = status
        self.updated_at = datetime.now().isoformat()
        
        if save:
            self.save()
    
    def is_active(self) -> bool:
        """检查标签是否活跃"""
        return self.status == self.STATUS_ACTIVE
    
    def is_assigned(self) -> bool:
        """检查标签是否已分配"""
        return bool(self.archive_id and self.archive_id.strip())
    
    def get_last_seen_info(self) -> Dict[str, Any]:
        """获取最后见到信息"""
        return {
            'location': self.last_seen_location or '未知',
            'time': self.last_seen_time or '从未扫描',
            'days_ago': self._calculate_days_since_last_seen()
        }
    
    def _calculate_days_since_last_seen(self) -> Optional[int]:
        """计算距离最后扫描的天数"""
        if not self.last_seen_time:
            return None
        
        try:
            last_seen = datetime.fromisoformat(self.last_seen_time)
            delta = datetime.now() - last_seen
            return delta.days
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """获取标签统计信息"""
        total_count = cls.count()
        active_count = cls.count("status = ?", [cls.STATUS_ACTIVE])
        assigned_count = cls.count("archive_id IS NOT NULL AND archive_id != ''")
        
        # 按类型统计
        type_stats = {}
        for tag_type in [cls.TYPE_ARCHIVE, cls.TYPE_LOCATION, cls.TYPE_EQUIPMENT]:
            count = cls.count("tag_type = ?", [tag_type])
            type_stats[tag_type] = count
        
        # 按状态统计
        status_stats = {}
        for status in [cls.STATUS_ACTIVE, cls.STATUS_INACTIVE, cls.STATUS_LOST, cls.STATUS_DAMAGED]:
            count = cls.count("status = ?", [status])
            status_stats[status] = count
        
        return {
            'total_count': total_count,
            'active_count': active_count,
            'assigned_count': assigned_count,
            'unassigned_count': total_count - assigned_count,
            'type_statistics': type_stats,
            'status_statistics': status_stats
        }