#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备维护记录模型
管理设备维护计划和维护历史记录
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from .base import BaseModel, ValidationError

class MaintenanceRecord(BaseModel):
    """设备维护记录模型"""
    
    # 设置表名
    table_name = 'maintenance_records'
    
    # 维护类型常量
    TYPE_ROUTINE = 'routine'          # 定期检查
    TYPE_PREVENTIVE = 'preventive'    # 预防性维护
    TYPE_CORRECTIVE = 'corrective'    # 故障维修
    TYPE_UPGRADE = 'upgrade'          # 设备升级
    TYPE_CALIBRATION = 'calibration'  # 设备校准
    
    # 维护状态常量
    STATUS_SCHEDULED = 'scheduled'    # 已计划
    STATUS_IN_PROGRESS = 'in_progress' # 进行中
    STATUS_COMPLETED = 'completed'    # 已完成
    STATUS_CANCELLED = 'cancelled'    # 已取消
    STATUS_OVERDUE = 'overdue'        # 已逾期
    
    # 设备类型常量
    DEVICE_RFID = 'rfid'             # RFID设备
    DEVICE_SENSOR = 'sensor'         # 传感器
    DEVICE_NETWORK = 'network'       # 网络设备
    DEVICE_SERVER = 'server'         # 服务器
    DEVICE_OTHER = 'other'           # 其他设备
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'MaintenanceRecord':
        """创建维护记录并进行验证"""
        instance = cls()
        
        # 验证必填字段
        required_fields = ['device_type', 'maintenance_type', 'description']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValidationError(f"字段 {field} 不能为空")
        
        # 验证设备类型
        valid_device_types = [cls.DEVICE_RFID, cls.DEVICE_SENSOR, 
                             cls.DEVICE_NETWORK, cls.DEVICE_SERVER, cls.DEVICE_OTHER]
        if kwargs['device_type'] not in valid_device_types:
            raise ValidationError(f"无效的设备类型: {kwargs['device_type']}")
        
        # 验证维护类型
        valid_maintenance_types = [cls.TYPE_ROUTINE, cls.TYPE_PREVENTIVE, 
                                 cls.TYPE_CORRECTIVE, cls.TYPE_UPGRADE, cls.TYPE_CALIBRATION]
        if kwargs['maintenance_type'] not in valid_maintenance_types:
            raise ValidationError(f"无效的维护类型: {kwargs['maintenance_type']}")
        
        # 验证状态
        if 'status' in kwargs:
            valid_statuses = [cls.STATUS_SCHEDULED, cls.STATUS_IN_PROGRESS, 
                            cls.STATUS_COMPLETED, cls.STATUS_CANCELLED, cls.STATUS_OVERDUE]
            if kwargs['status'] not in valid_statuses:
                raise ValidationError(f"无效的维护状态: {kwargs['status']}")
        
        # 验证日期格式
        if 'scheduled_date' in kwargs and kwargs['scheduled_date']:
            try:
                if isinstance(kwargs['scheduled_date'], str):
                    datetime.fromisoformat(kwargs['scheduled_date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("计划日期格式无效")
        
        if 'completed_date' in kwargs and kwargs['completed_date']:
            try:
                if isinstance(kwargs['completed_date'], str):
                    datetime.fromisoformat(kwargs['completed_date'].replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("完成日期格式无效")
        
        # 验证费用
        if 'cost' in kwargs and kwargs['cost'] is not None:
            try:
                float(kwargs['cost'])
                if float(kwargs['cost']) < 0:
                    raise ValidationError("维护费用不能为负数")
            except (ValueError, TypeError):
                raise ValidationError("维护费用必须是有效数字")
        
        # 创建记录
        record = instance.__class__.create(**kwargs)
        return record
    
    def create_record(self, **kwargs) -> 'MaintenanceRecord':
        """创建维护记录"""
        # 设置默认值
        kwargs.setdefault('status', self.STATUS_SCHEDULED)
        kwargs.setdefault('cost', 0.0)
        kwargs.setdefault('created_at', datetime.now().isoformat())
        
        return self.__class__.create(**kwargs)
    
    @classmethod
    def find_by_device(cls, device_type: str, device_id: int = None) -> List[Dict[str, Any]]:
        """根据设备查找维护记录"""
        if device_id:
            where_clause = "device_type = ? AND device_id = ?"
            params = [device_type, device_id]
        else:
            where_clause = "device_type = ?"
            params = [device_type]
        
        records = cls.find_all(where_clause, params, order_by="scheduled_date DESC")
        return [record.data for record in records]
    
    @classmethod
    def find_by_status(cls, status: str) -> List[Dict[str, Any]]:
        """根据状态查找维护记录"""
        records = cls.find_all("status = ?", [status], order_by="scheduled_date ASC")
        return [record.data for record in records]
    
    @classmethod
    def find_overdue(cls) -> List[Dict[str, Any]]:
        """查找逾期的维护记录"""
        current_time = datetime.now().isoformat()
        where_clause = "status = ? AND scheduled_date < ?"
        params = [cls.STATUS_SCHEDULED, current_time]
        
        records = cls.find_all(where_clause, params, order_by="scheduled_date ASC")
        return [record.data for record in records]
    
    @classmethod
    def find_upcoming(cls, days: int = 7) -> List[Dict[str, Any]]:
        """查找即将到期的维护记录"""
        current_time = datetime.now()
        future_time = current_time + timedelta(days=days)
        
        where_clause = "status = ? AND scheduled_date BETWEEN ? AND ?"
        params = [cls.STATUS_SCHEDULED, current_time.isoformat(), future_time.isoformat()]
        
        records = cls.find_all(where_clause, params, order_by="scheduled_date ASC")
        return [record.data for record in records]
    
    @classmethod
    def update_status(cls, record_id: int, status: str, notes: str = None) -> bool:
        """更新维护记录状态"""
        valid_statuses = [cls.STATUS_SCHEDULED, cls.STATUS_IN_PROGRESS, 
                         cls.STATUS_COMPLETED, cls.STATUS_CANCELLED, cls.STATUS_OVERDUE]
        if status not in valid_statuses:
            raise ValidationError(f"无效的维护状态: {status}")
        
        # 查找记录
        record = cls.find_by_id(record_id)
        if not record:
            return False
        
        # 更新状态
        record.status = status
        
        # 如果标记为完成，设置完成时间
        if status == cls.STATUS_COMPLETED:
            record.completed_date = datetime.now().isoformat()
        
        # 添加备注
        if notes:
            record.notes = notes
        
        return record.save()
    
    @classmethod
    def get_statistics(cls, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """获取维护统计信息"""
        from database import execute_query
        
        # 基础查询条件
        where_clause = "1=1"
        params = []
        
        if start_date:
            where_clause += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            where_clause += " AND created_at <= ?"
            params.append(end_date)
        
        # 总记录数
        total_result = execute_query(f'''
            SELECT COUNT(*) as total FROM maintenance_records 
            WHERE {where_clause}
        ''', params, fetch_one=True, fetch_all=False)
        total = total_result['total'] if total_result else 0
        
        # 按状态统计
        status_results = execute_query(f'''
            SELECT status, COUNT(*) as count FROM maintenance_records 
            WHERE {where_clause}
            GROUP BY status
        ''', params, fetch_one=False, fetch_all=True)
        status_stats = {row['status']: row['count'] for row in status_results}
        
        # 按设备类型统计
        device_results = execute_query(f'''
            SELECT device_type, COUNT(*) as count FROM maintenance_records 
            WHERE {where_clause}
            GROUP BY device_type
        ''', params, fetch_one=False, fetch_all=True)
        device_stats = {row['device_type']: row['count'] for row in device_results}
        
        # 按维护类型统计
        type_results = execute_query(f'''
            SELECT maintenance_type, COUNT(*) as count FROM maintenance_records 
            WHERE {where_clause}
            GROUP BY maintenance_type
        ''', params, fetch_one=False, fetch_all=True)
        type_stats = {row['maintenance_type']: row['count'] for row in type_results}
        
        # 费用统计
        cost_result = execute_query(f'''
            SELECT 
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost,
                MAX(cost) as max_cost,
                MIN(cost) as min_cost
            FROM maintenance_records 
            WHERE {where_clause} AND cost > 0
        ''', params, fetch_one=True, fetch_all=False)
        
        cost_stats = {
            'total_cost': cost_result['total_cost'] or 0 if cost_result else 0,
            'avg_cost': cost_result['avg_cost'] or 0 if cost_result else 0,
            'max_cost': cost_result['max_cost'] or 0 if cost_result else 0,
            'min_cost': cost_result['min_cost'] or 0 if cost_result else 0
        }
        
        return {
            'total': total,
            'by_status': status_stats,
            'by_device_type': device_stats,
            'by_maintenance_type': type_stats,
            'cost_statistics': cost_stats,
            'overdue_count': len(cls.find_overdue()),
            'upcoming_count': len(cls.find_upcoming())
        }
    
    @classmethod
    def search(cls, keyword: str = None, device_type: str = None, 
               maintenance_type: str = None, status: str = None,
               start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """搜索维护记录"""
        where_conditions = []
        params = []
        
        if keyword:
            where_conditions.append("(description LIKE ? OR technician LIKE ? OR notes LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        
        if device_type:
            where_conditions.append("device_type = ?")
            params.append(device_type)
        
        if maintenance_type:
            where_conditions.append("maintenance_type = ?")
            params.append(maintenance_type)
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        if start_date:
            where_conditions.append("scheduled_date >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("scheduled_date <= ?")
            params.append(end_date)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        records = cls.find_all(where_clause, params, order_by="scheduled_date DESC")
        return [record.data for record in records]