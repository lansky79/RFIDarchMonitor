#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据模型类
提供通用的数据库操作方法
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from database import get_db_connection, execute_query

logger = logging.getLogger(__name__)

class BaseModel:
    """基础模型类，提供通用的数据库操作方法"""
    
    # 子类需要定义的属性
    table_name = None
    primary_key = 'id'
    
    def __init__(self, **kwargs):
        """初始化模型实例"""
        self.data = kwargs
        self._original_data = kwargs.copy()
    
    def __getattr__(self, name):
        """获取属性值"""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """设置属性值"""
        if name in ['data', '_original_data', 'table_name', 'primary_key']:
            super().__setattr__(name, value)
        else:
            if not hasattr(self, 'data'):
                super().__setattr__(name, value)
            else:
                self.data[name] = value
    
    @classmethod
    def create(cls, **kwargs) -> 'BaseModel':
        """创建新记录"""
        if not cls.table_name:
            raise ValueError(f"{cls.__name__} must define table_name")
        
        # 添加创建时间
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now().isoformat()
        
        # 构建插入SQL
        columns = list(kwargs.keys())
        placeholders = ['?' for _ in columns]
        values = list(kwargs.values())
        
        sql = f"""
            INSERT INTO {cls.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        try:
            record_id = execute_query(sql, values, fetch_one=False, fetch_all=False)
            kwargs[cls.primary_key] = record_id
            
            logger.info(f"创建{cls.__name__}记录成功: ID={record_id}")
            return cls(**kwargs)
            
        except Exception as e:
            logger.error(f"创建{cls.__name__}记录失败: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, record_id: Union[int, str]) -> Optional['BaseModel']:
        """根据ID查找记录"""
        if not cls.table_name:
            raise ValueError(f"{cls.__name__} must define table_name")
        
        sql = f"SELECT * FROM {cls.table_name} WHERE {cls.primary_key} = ?"
        
        try:
            result = execute_query(sql, [record_id], fetch_one=True, fetch_all=False)
            return cls(**result) if result else None
            
        except Exception as e:
            logger.error(f"查找{cls.__name__}记录失败: {e}")
            raise
    
    @classmethod
    def find_all(cls, where_clause: str = None, params: List = None, 
                 order_by: str = None, limit: int = None) -> List['BaseModel']:
        """查找所有记录"""
        if not cls.table_name:
            raise ValueError(f"{cls.__name__} must define table_name")
        
        sql = f"SELECT * FROM {cls.table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        try:
            results = execute_query(sql, params or [], fetch_one=False, fetch_all=True)
            return [cls(**result) for result in results]
            
        except Exception as e:
            logger.error(f"查找{cls.__name__}记录失败: {e}")
            raise
    
    @classmethod
    def find_one(cls, where_clause: str, params: List = None) -> Optional['BaseModel']:
        """查找单条记录"""
        results = cls.find_all(where_clause, params, limit=1)
        return results[0] if results else None
    
    @classmethod
    def count(cls, where_clause: str = None, params: List = None) -> int:
        """统计记录数量"""
        if not cls.table_name:
            raise ValueError(f"{cls.__name__} must define table_name")
        
        sql = f"SELECT COUNT(*) as count FROM {cls.table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        try:
            result = execute_query(sql, params or [], fetch_one=True, fetch_all=False)
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"统计{cls.__name__}记录失败: {e}")
            raise
    
    def save(self) -> bool:
        """保存记录（更新或插入）"""
        if not self.table_name:
            raise ValueError(f"{self.__class__.__name__} must define table_name")
        
        try:
            if self.primary_key in self.data and self.data[self.primary_key]:
                return self._update()
            else:
                return self._insert()
                
        except Exception as e:
            logger.error(f"保存{self.__class__.__name__}记录失败: {e}")
            raise
    
    def _insert(self) -> bool:
        """插入新记录"""
        # 添加创建时间
        if 'created_at' not in self.data:
            self.data['created_at'] = datetime.now().isoformat()
        
        columns = list(self.data.keys())
        placeholders = ['?' for _ in columns]
        values = list(self.data.values())
        
        sql = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        record_id = execute_query(sql, values, fetch_one=False, fetch_all=False)
        self.data[self.primary_key] = record_id
        self._original_data = self.data.copy()
        
        logger.info(f"插入{self.__class__.__name__}记录成功: ID={record_id}")
        return True
    
    def _update(self) -> bool:
        """更新现有记录"""
        # 只更新已修改的字段
        changed_fields = {}
        for key, value in self.data.items():
            if key != self.primary_key and value != self._original_data.get(key):
                changed_fields[key] = value
        
        if not changed_fields:
            logger.info(f"{self.__class__.__name__}记录无变更，跳过更新")
            return True
        
        # 添加更新时间
        if 'updated_at' not in changed_fields:
            changed_fields['updated_at'] = datetime.now().isoformat()
            self.data['updated_at'] = changed_fields['updated_at']
        
        set_clause = ', '.join([f"{key} = ?" for key in changed_fields.keys()])
        values = list(changed_fields.values())
        values.append(self.data[self.primary_key])
        
        sql = f"""
            UPDATE {self.table_name} 
            SET {set_clause}
            WHERE {self.primary_key} = ?
        """
        
        execute_query(sql, values, fetch_one=False, fetch_all=False)
        self._original_data = self.data.copy()
        
        logger.info(f"更新{self.__class__.__name__}记录成功: ID={self.data[self.primary_key]}")
        return True
    
    def delete(self) -> bool:
        """删除记录"""
        if not self.table_name:
            raise ValueError(f"{self.__class__.__name__} must define table_name")
        
        if self.primary_key not in self.data or not self.data[self.primary_key]:
            raise ValueError("无法删除未保存的记录")
        
        sql = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
        
        try:
            execute_query(sql, [self.data[self.primary_key]], fetch_one=False, fetch_all=False)
            logger.info(f"删除{self.__class__.__name__}记录成功: ID={self.data[self.primary_key]}")
            return True
            
        except Exception as e:
            logger.error(f"删除{self.__class__.__name__}记录失败: {e}")
            raise
    
    @classmethod
    def delete_by_id(cls, record_id: Union[int, str]) -> bool:
        """根据ID删除记录"""
        if not cls.table_name:
            raise ValueError(f"{cls.__name__} must define table_name")
        
        sql = f"DELETE FROM {cls.table_name} WHERE {cls.primary_key} = ?"
        
        try:
            execute_query(sql, [record_id], fetch_one=False, fetch_all=False)
            logger.info(f"删除{cls.__name__}记录成功: ID={record_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除{cls.__name__}记录失败: {e}")
            raise
    
    @classmethod
    def execute_raw_sql(cls, sql: str, params: List = None, 
                       fetch_one: bool = False, fetch_all: bool = True) -> Any:
        """执行原始SQL查询"""
        try:
            return execute_query(sql, params or [], fetch_one=fetch_one, fetch_all=fetch_all)
        except Exception as e:
            logger.error(f"执行SQL失败: {sql}, 错误: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.data.copy()
    
    def to_json_dict(self) -> Dict[str, Any]:
        """转换为JSON兼容的字典"""
        result = {}
        for key, value in self.data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    def __repr__(self):
        """字符串表示"""
        class_name = self.__class__.__name__
        if self.primary_key in self.data:
            return f"<{class_name}(id={self.data[self.primary_key]})>"
        else:
            return f"<{class_name}(unsaved)>"
    
    def __str__(self):
        """字符串表示"""
        return self.__repr__()


class ValidationError(Exception):
    """数据验证错误"""
    pass


class DatabaseError(Exception):
    """数据库操作错误"""
    pass


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """验证必填字段"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"缺少必填字段: {', '.join(missing_fields)}")


def validate_field_length(data: Dict[str, Any], field_limits: Dict[str, int]) -> None:
    """验证字段长度"""
    for field, max_length in field_limits.items():
        if field in data and data[field] and len(str(data[field])) > max_length:
            raise ValidationError(f"字段 {field} 长度超过限制 ({max_length} 字符)")


def validate_numeric_range(data: Dict[str, Any], field_ranges: Dict[str, tuple]) -> None:
    """验证数值范围"""
    for field, (min_val, max_val) in field_ranges.items():
        if field in data and data[field] is not None:
            try:
                value = float(data[field])
                if value < min_val or value > max_val:
                    raise ValidationError(f"字段 {field} 值超出范围 ({min_val} - {max_val})")
            except (ValueError, TypeError):
                raise ValidationError(f"字段 {field} 必须是数值类型")