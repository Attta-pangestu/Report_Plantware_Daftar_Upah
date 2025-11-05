#!/usr/bin/env python3
"""
Query Executor - Advanced SQL Query Execution with ORM-like Features
Provides high-level query execution with parameterized queries, result mapping, and query building
"""

import pyodbc
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime

from connection_manager import ConnectionManager


class QueryType(Enum):
    """Query types for different operations"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STORED_PROCEDURE = "EXECUTE"


@dataclass
class QueryResult:
    """Query result wrapper with metadata"""
    data: List[Dict[str, Any]]
    affected_rows: int
    execution_time: float
    query_type: QueryType
    columns: List[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class QueryParameter:
    """Query parameter with type information"""
    name: str
    value: Any
    data_type: Optional[str] = None
    size: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


class QueryBuilder:
    """SQL Query Builder for common operations"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset query builder"""
        self._table = None
        self._select_fields = []
        self._where_conditions = []
        self._joins = []
        self._group_by = []
        self._having = []
        self._order_by = []
        self._limit = None
        self._offset = None
        self._parameters = []

    def table(self, table: str) -> 'QueryBuilder':
        """Set table name"""
        self._table = table
        return self

    def select(self, *fields: str) -> 'QueryBuilder':
        """Add SELECT fields"""
        self._select_fields.extend(fields)
        return self

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add WHERE condition"""
        self._where_conditions.append(condition)
        self._parameters.extend(params)
        return self

    def join(self, table: str, condition: str, join_type: str = "INNER") -> 'QueryBuilder':
        """Add JOIN clause"""
        self._joins.append(f"{join_type} JOIN {table} ON {condition}")
        return self

    def left_join(self, table: str, condition: str) -> 'QueryBuilder':
        """Add LEFT JOIN"""
        return self.join(table, condition, "LEFT")

    def right_join(self, table: str, condition: str) -> 'QueryBuilder':
        """Add RIGHT JOIN"""
        return self.join(table, condition, "RIGHT")

    def group_by(self, *fields: str) -> 'QueryBuilder':
        """Add GROUP BY fields"""
        self._group_by.extend(fields)
        return self

    def having(self, condition: str, *params: Any) -> 'QueryBuilder':
        """Add HAVING condition"""
        self._having.append(condition)
        self._parameters.extend(params)
        return self

    def order_by(self, field: str, direction: str = "ASC") -> 'QueryBuilder':
        """Add ORDER BY field"""
        self._order_by.append(f"{field} {direction}")
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """Set LIMIT"""
        self._limit = limit
        return self

    def offset(self, offset: int) -> 'QueryBuilder':
        """Set OFFSET"""
        self._offset = offset
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """Build final query and return SQL and parameters"""
        if not self._table:
            raise ValueError("Table name is required")

        # Build SELECT clause
        if self._select_fields:
            select_clause = f"SELECT {', '.join(self._select_fields)}"
        else:
            select_clause = "SELECT *"

        # Build FROM clause
        from_clause = f"FROM {self._table}"

        # Build JOIN clauses
        join_clause = ""
        if self._joins:
            join_clause = " " + " ".join(self._joins)

        # Build WHERE clause
        where_clause = ""
        if self._where_conditions:
            where_clause = " WHERE " + " AND ".join(self._where_conditions)

        # Build GROUP BY clause
        group_by_clause = ""
        if self._group_by:
            group_by_clause = " GROUP BY " + ", ".join(self._group_by)

        # Build HAVING clause
        having_clause = ""
        if self._having:
            having_clause = " HAVING " + " AND ".join(self._having)

        # Build ORDER BY clause
        order_by_clause = ""
        if self._order_by:
            order_by_clause = " ORDER BY " + ", ".join(self._order_by)

        # Build LIMIT/OFFSET clause (SQL Server syntax)
        limit_clause = ""
        if self._limit is not None:
            if self._offset is not None:
                limit_clause = f" OFFSET {self._offset} ROWS FETCH NEXT {self._limit} ROWS ONLY"
            else:
                limit_clause = f" TOP ({self._limit})"

        # Combine all clauses
        query = f"{select_clause} {from_clause}{join_clause}{where_clause}{group_by_clause}{having_clause}{order_by_clause}{limit_clause}"

        return query, self._parameters


class QueryExecutor:
    """
    Advanced Query Executor with ORM-like features

    Provides:
    - Parameterized queries
    - Result mapping and transformation
    - Query building
    - Batch operations
    - Transaction management
    - Query logging and performance tracking
    """

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize query executor

        Args:
            connection_manager: Database connection manager instance
        """
        self.connection_manager = connection_manager
        self.query_log = []
        self.performance_stats = {
            'total_queries': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'slow_queries': 0,
            'failed_queries': 0
        }

    def execute_query(self, query: str, params: Optional[List[Any]] = None,
                      fetch_mode: str = "all", query_type: QueryType = QueryType.SELECT) -> QueryResult:
        """
        Execute SQL query with advanced features

        Args:
            query: SQL query string
            params: Query parameters
            fetch_mode: Fetch mode ("all", "one", "many", "scalar", "cursor")
            query_type: Type of query being executed

        Returns:
            QueryResult: Query result with metadata
        """
        start_time = datetime.now()

        try:
            # Convert parameters list to tuple if needed
            if params is not None and not isinstance(params, tuple):
                params = tuple(params)

            # Log query
            self._log_query(query, params, start_time)

            # Execute query based on fetch mode
            if fetch_mode == "cursor":
                # Return cursor for advanced operations
                with self.connection_manager.get_connection() as conn:
                    cursor = conn.execute(query, params)
                    result = QueryResult(
                        data=[],
                        affected_rows=cursor.rowcount,
                        execution_time=(datetime.now() - start_time).total_seconds(),
                        query_type=query_type,
                        columns=[col[0] for col in cursor.description] if cursor.description else [],
                        success=True,
                        error_message=None
                    )
                    result._cursor = cursor  # Store cursor reference
                    return result

            else:
                # Standard execution
                if fetch_mode == "all":
                    data = self.connection_manager.execute_query(query, params, "all")
                elif fetch_mode == "one":
                    data = self.connection_manager.execute_query(query, params, "one")
                    data = [data] if data is not None else []
                elif fetch_mode == "many":
                    data = self.connection_manager.execute_query(query, params, "many")
                elif fetch_mode == "scalar":
                    scalar_result = self.connection_manager.execute_query(query, params, "scalar")
                    data = [[scalar_result]] if scalar_result is not None else []
                else:
                    raise ValueError(f"Invalid fetch_mode: {fetch_mode}")

                # Get columns from first row if data exists
                columns = list(data[0].keys()) if data else []

                execution_time = (datetime.now() - start_time).total_seconds()

                result = QueryResult(
                    data=data,
                    affected_rows=len(data),
                    execution_time=execution_time,
                    query_type=query_type,
                    columns=columns,
                    success=True,
                    error_message=None
                )

                # Update performance stats
                self._update_performance_stats(execution_time, True)

                return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)

            result = QueryResult(
                data=[],
                affected_rows=0,
                execution_time=execution_time,
                query_type=query_type,
                columns=[],
                success=False,
                error_message=error_message
            )

            # Update performance stats
            self._update_performance_stats(execution_time, False)

            raise e

    def execute_stored_procedure(self, procedure_name: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute stored procedure

        Args:
            procedure_name: Name of stored procedure
            params: Procedure parameters

        Returns:
            QueryResult: Procedure execution result
        """
        if params is None:
            query = f"EXEC {procedure_name}"
            proc_params = []
        else:
            param_list = []
            proc_params = []
            for key, value in params.items():
                param_list.append(f"@{key}=?")
                proc_params.append(value)
            query = f"EXEC {procedure_name} {', '.join(param_list)}"

        return self.execute_query(query, proc_params, QueryType.STORED_PROCEDURE)

    def select(self, table: str, where_clause: Optional[str] = None, params: Optional[List[Any]] = None,
               order_by: Optional[str] = None, limit: Optional[int] = None) -> QueryResult:
        """
        Execute SELECT query with simplified syntax

        Args:
            table: Table name
            where_clause: WHERE clause
            params: WHERE parameters
            order_by: ORDER BY clause
            limit: LIMIT value

        Returns:
            QueryResult: Select query result
        """
        query = f"SELECT * FROM {table}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" TOP ({limit})"

        return self.execute_query(query, params, QueryType.SELECT)

    def insert(self, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> QueryResult:
        """
        Execute INSERT query

        Args:
            table: Table name
            data: Data to insert (dict or list of dicts)

        Returns:
            QueryResult: Insert query result
        """
        if isinstance(data, dict):
            data = [data]

        if not data:
            raise ValueError("No data provided for insert")

        # Get columns from first record
        columns = list(data[0].keys())
        placeholders = ["?" for _ in columns]
        values_list = []

        # Prepare values for each record
        for record in data:
            values = [record.get(col) for col in columns]
            values_list.append(values)

        # Build query
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders_str})"

        if len(values_list) == 1:
            return self.execute_query(query, values_list[0], QueryType.INSERT)
        else:
            # Batch insert
            return self.execute_batch([(query, values) for values in values_list], QueryType.INSERT)

    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Optional[List[Any]] = None) -> QueryResult:
        """
        Execute UPDATE query

        Args:
            table: Table name
            data: Data to update
            where_clause: WHERE clause
            where_params: WHERE parameters

        Returns:
            QueryResult: Update query result
        """
        # Build SET clause
        set_clauses = []
        params = []

        for column, value in data.items():
            set_clauses.append(f"{column} = ?")
            params.append(value)

        # Add WHERE parameters
        if where_params:
            params.extend(where_params)

        # Build query
        set_clause = ", ".join(set_clauses)
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        return self.execute_query(query, params, QueryType.UPDATE)

    def delete(self, table: str, where_clause: str, where_params: Optional[List[Any]] = None) -> QueryResult:
        """
        Execute DELETE query

        Args:
            table: Table name
            where_clause: WHERE clause
            where_params: WHERE parameters

        Returns:
            QueryResult: Delete query result
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        return self.execute_query(query, where_params, QueryType.DELETE)

    def execute_batch(self, queries: List[Tuple[str, List[Any]]], query_type: QueryType = QueryType.SELECT) -> QueryResult:
        """
        Execute multiple queries in a transaction

        Args:
            queries: List of (query, params) tuples
            query_type: Type of queries being executed

        Returns:
            QueryResult: Batch execution result
        """
        start_time = datetime.now()

        try:
            all_results = []

            # Use connection manager's batch execution
            raw_results = self.connection_manager.execute_batch(queries)

            for raw_result in raw_results:
                query_result = QueryResult(
                    data=raw_result,
                    affected_rows=len(raw_result),
                    execution_time=0,  # Will be calculated later
                    query_type=query_type,
                    columns=list(raw_result[0].keys()) if raw_result else [],
                    success=True,
                    error_message=None
                )
                all_results.append(query_result)

            total_execution_time = (datetime.now() - start_time).total_seconds()
            total_affected = sum(result.affected_rows for result in all_results)

            # Combine all results
            combined_data = []
            for result in all_results:
                combined_data.extend(result.data)

            result = QueryResult(
                data=combined_data,
                affected_rows=total_affected,
                execution_time=total_execution_time,
                query_type=query_type,
                columns=list(set().union(*[result.columns for result in all_results])),
                success=True,
                error_message=None
            )

            # Update performance stats
            self._update_performance_stats(total_execution_time, True)

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)

            result = QueryResult(
                data=[],
                affected_rows=0,
                execution_time=execution_time,
                query_type=query_type,
                columns=[],
                success=False,
                error_message=error_message
            )

            # Update performance stats
            self._update_performance_stats(execution_time, False)

            raise e

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table information including columns, indexes, etc.

        Args:
            table_name: Table name

        Returns:
            Dictionary with table information
        """
        info = {}

        try:
            # Get column information
            columns_query = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """

            result = self.execute_query(columns_query, [table_name])
            info['columns'] = result.data

            # Get primary key information
            pk_query = """
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                AND tc.TABLE_NAME = ?
            """

            result = self.execute_query(pk_query, [table_name])
            info['primary_key'] = [col['COLUMN_NAME'] for col in result.data]

            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            result = self.execute_query(count_query)
            info['row_count'] = result.data[0]['row_count'] if result.data else 0

        except Exception as e:
            info['error'] = str(e)

        return info

    def get_database_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get complete database schema information

        Returns:
            Dictionary with schema information
        """
        schema = {}

        try:
            # Get all tables
            tables_query = """
            SELECT TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """

            result = self.execute_query(tables_query)

            for table_info in result.data:
                table_name = table_info['TABLE_NAME']
                schema[table_name] = self.get_table_info(table_name)

        except Exception as e:
            schema['error'] = str(e)

        return schema

    def create_query_builder(self) -> QueryBuilder:
        """
        Create a new query builder instance

        Returns:
            QueryBuilder: New query builder instance
        """
        return QueryBuilder()

    def analyze_query_performance(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Analyze query performance using execution plan

        Args:
            query: SQL query to analyze
            params: Query parameters

        Returns:
            Dictionary with performance analysis
        """
        analysis = {}

        try:
            # Get execution plan
            plan_query = f"SET SHOWPLAN_TEXT ON; {query}; SET SHOWPLAN_TEXT OFF"
            plan_result = self.execute_query(plan_query, params)

            analysis['execution_plan'] = plan_result.data
            analysis['estimated_cost'] = self._extract_estimated_cost(plan_result.data)

            # Get actual execution statistics
            stats_query = f"SET STATISTICS TIME ON; {query}; SET STATISTICS TIME OFF"
            start_time = datetime.now()
            self.execute_query(stats_query, params)
            actual_time = (datetime.now() - start_time).total_seconds()

            analysis['actual_execution_time'] = actual_time

        except Exception as e:
            analysis['error'] = str(e)

        return analysis

    def _log_query(self, query: str, params: Optional[List[Any]], start_time: datetime):
        """Log query for debugging and performance tracking"""
        log_entry = {
            'timestamp': start_time.isoformat(),
            'query': query,
            'params': params,
            'query_hash': self._generate_query_hash(query)
        }

        self.query_log.append(log_entry)

        # Keep only last 1000 queries in memory
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-1000:]

    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query identification"""
        # Remove parameter placeholders and whitespace
        clean_query = re.sub(r'[?]', '', query)
        clean_query = re.sub(r'\s+', ' ', clean_query).strip()
        return str(hash(clean_query))

    def _update_performance_stats(self, execution_time: float, success: bool):
        """Update performance statistics"""
        self.performance_stats['total_queries'] += 1
        self.performance_stats['total_time'] += execution_time
        self.performance_stats['average_time'] = (
            self.performance_stats['total_time'] / self.performance_stats['total_queries']
        )

        if execution_time > 1.0:  # Consider queries over 1 second as slow
            self.performance_stats['slow_queries'] += 1

        if not success:
            self.performance_stats['failed_queries'] += 1

    def _extract_estimated_cost(self, plan_data: List[Dict[str, Any]]) -> Optional[float]:
        """Extract estimated cost from execution plan"""
        for row in plan_data:
            if 'StmtText' in row:
                text = row['StmtText']
                # Look for cost information in plan text
                cost_match = re.search(r'Cost: ([\d.]+)', text)
                if cost_match:
                    return float(cost_match.group(1))
        return None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.performance_stats,
            'queries_in_log': len(self.query_log),
            'success_rate': (
                (self.performance_stats['total_queries'] - self.performance_stats['failed_queries']) /
                self.performance_stats['total_queries'] * 100
            ) if self.performance_stats['total_queries'] > 0 else 0
        }

    def clear_query_log(self):
        """Clear query log"""
        self.query_log.clear()

    def get_slow_queries(self, threshold_seconds: float = 1.0) -> List[Dict[str, Any]]:
        """Get list of slow queries from log"""
        # Note: This would require timing information to be stored in the log
        # For now, return queries that would likely be slow based on analysis
        slow_queries = []

        for log_entry in self.query_log:
            query = log_entry['query']
            # Simple heuristic for slow queries
            if any(keyword in query.upper() for keyword in ['JOIN', 'GROUP BY', 'ORDER BY', 'SUBQUERY']):
                slow_queries.append(log_entry)

        return slow_queries


def main():
    """Test query executor"""
    print("=" * 60)
    print("QUERY EXECUTOR TEST")
    print("=" * 60)

    try:
        from connection_manager import ConnectionManager

        # Initialize connection manager and query executor
        with ConnectionManager() as conn_manager:
            query_executor = QueryExecutor(conn_manager)

            print("[OK] Query executor initialized")

            # Test simple select
            print("\n1. Testing simple SELECT query...")
            result = query_executor.select("sys.tables", "TABLE_TYPE = 'BASE TABLE'", ["BASE TABLE"], "TABLE_NAME", 5)
            print(f"   Found {result.affected_rows} tables")
            print(f"   Query time: {result.execution_time:.3f}s")
            print(f"   Columns: {result.columns}")

            # Test query builder
            print("\n2. Testing query builder...")
            builder = query_executor.create_query_builder()
            query, params = builder.table("sys.tables")\
                .select("name", "create_date")\
                .where("TABLE_TYPE = ?", "BASE TABLE")\
                .order_by("create_date", "DESC")\
                .limit(3)\
                .build()

            print(f"   Built query: {query}")
            print(f"   Parameters: {params}")

            result = query_executor.execute_query(query, params)
            print(f"   Results: {len(result.data)} rows")

            # Test stored procedure execution
            print("\n3. Testing stored procedure execution...")
            try:
                result = query_executor.execute_stored_procedure("sp_who", [])
                print(f"   Procedure results: {len(result.data)} rows")
            except Exception as e:
                print(f"   Procedure test skipped: {e}")

            # Get performance stats
            print("\n4. Performance statistics:")
            stats = query_executor.get_performance_stats()
            print(f"   Total queries: {stats['total_queries']}")
            print(f"   Average time: {stats['average_time']:.3f}s")
            print(f"   Success rate: {stats['success_rate']:.1f}%")

            # Get table info
            print("\n5. Getting table information...")
            try:
                table_info = query_executor.get_table_info("sys.tables")
                print(f"   Columns in sys.tables: {len(table_info.get('columns', []))}")
                print(f"   Primary key: {table_info.get('primary_key', [])}")
                print(f"   Row count: {table_info.get('row_count', 0)}")
            except Exception as e:
                print(f"   Table info test skipped: {e}")

        print("\n[OK] Query executor test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Query executor test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()