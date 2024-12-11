import React, { useState, useEffect } from 'react';
import { Table, Input, Button, Popover, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const EditableTable = ({ selectedFile, removeFile, styles }) => {
  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [editingHeader, setEditingHeader] = useState(null);
  const [newColumnName, setNewColumnName] = useState('');

  // Initialize table when CSV file is loaded
  useEffect(() => {
    if (selectedFile && selectedFile.length > 0) {
      const fileColumns = Object.keys(selectedFile[0]);
      setColumns(fileColumns);
      setData(selectedFile.map((row, index) => ({ 
        ...row, 
        key: index.toString() 
      })));
    } else {
      // Default empty table
      const initialColumns = ['Biomarker 1', 'Biomarker 2'];
      setColumns(initialColumns);
      setData([createEmptyRow(initialColumns)]);
    }
  }, [selectedFile]);

  const createEmptyRow = (columnList) => {
    const row = { key: Date.now().toString() };
    columnList.forEach(col => row[col] = '');
    return row;
  };

  const handleCellChange = (key, column, value) => {
    const newData = [...data];
    const index = newData.findIndex(item => item.key === key);
    if (index > -1) {
      const item = newData[index];
      newData.splice(index, 1, {
        ...item,
        [column]: value,
      });
      setData(newData);
    }
  };

  const handleColumnNameChange = (oldName, newName) => {
    if (!newName || newName === oldName) {
      setEditingHeader(null);
      return;
    }

    const newColumns = columns.map(col => col === oldName ? newName : col);
    setColumns(newColumns);

    const newData = data.map(row => {
      const updatedRow = { ...row };
      updatedRow[newName] = row[oldName];
      delete updatedRow[oldName];
      return updatedRow;
    });
    setData(newData);

    setEditingHeader(null);
  };

  // Verbose delete column handler with error catching and logging
  const handleDeleteColumn = (columnToDelete) => {
    try {
      console.log('Delete column called with:', columnToDelete);
      console.log('Current columns:', columns);
      console.log('Current data:', data);

      // Prevent deletion if only one column remains
      if (columns.length <= 1) {
        message.error('Cannot delete the last column');
        return;
      }

      // Validate column exists
      if (!columns.includes(columnToDelete)) {
        message.error(`Column "${columnToDelete}" not found`);
        return;
      }

      // Filter out the column from columns
      const newColumns = columns.filter(col => col !== columnToDelete);
      console.log('New columns:', newColumns);

      // Remove the column from each row's data
      const newData = data.map(row => {
        const updatedRow = { ...row };
        delete updatedRow[columnToDelete];
        return updatedRow;
      });
      console.log('New data:', newData);

      // Update state
      setColumns(newColumns);
      setData(newData);

      // Show success message
      message.success(`Column "${columnToDelete}" deleted`);
    } catch (error) {
      console.error('Error deleting column:', error);
      message.error('Failed to delete column');
    }
  };

  // Configure table columns with explicit delete handler
  const tableColumns = columns.map(column => ({
    title: (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        width: '100%'
      }}>
        {editingHeader === column ? (
          <Input
            defaultValue={column}
            onPressEnter={(e) => handleColumnNameChange(column, e.target.value)}
            onBlur={(e) => handleColumnNameChange(column, e.target.value)}
            autoFocus
          />
        ) : (
          <span>{column}</span>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <EditOutlined 
            onClick={(e) => {
              e.stopPropagation();
              setEditingHeader(column);
            }}
            style={{ cursor: 'pointer', fontSize: '14px' }}
          />
          <DeleteOutlined 
            onClick={(e) => {
              e.stopPropagation(); // Prevent event bubbling
              console.log('Delete icon clicked for column:', column);
              handleDeleteColumn(column);
            }}
            style={{ 
              cursor: 'pointer', 
              fontSize: '14px', 
              color: '#ff4d4f' 
            }}
          />
        </div>
      </div>
    ),
    dataIndex: column,
    key: column,
    render: (text, record) => (
      <Input
        value={text}
        onChange={e => handleCellChange(record.key, column, e.target.value)}
        onClick={e => e.stopPropagation()}
      />
    ),
  }));

  // Add Column popover content
  const addColumnContent = (
    <div style={{ padding: '8px', width: 250 }}>
      <Input
        placeholder="Enter biomarker name"
        value={newColumnName}
        onChange={e => setNewColumnName(e.target.value)}
        style={{ marginBottom: '8px' }}
      />
      <Button type="primary" onClick={() => {
        const columnName = newColumnName.trim() || `Column ${columns.length + 1}`;
        setColumns(prev => [...prev, columnName]);
        setData(prev => prev.map(row => ({
          ...row,
          [columnName]: ''
        })));
        setNewColumnName('');
      }} block>
        Add Biomarker
      </Button>
    </div>
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Popover 
          content={addColumnContent} 
          title="Add New Biomarker" 
          trigger="click"
        >
          <Button icon={<PlusOutlined />}>
            Add Biomarker
          </Button>
        </Popover>

        {selectedFile && (
          <Button 
            danger
            onClick={removeFile}
          >
            Remove File
          </Button>
        )}
      </div>

      <Table 
        dataSource={data} 
        columns={tableColumns} 
        pagination={false}
        bordered
        scroll={{ x: true }}
      />
    </div>
  );
};

export default EditableTable;