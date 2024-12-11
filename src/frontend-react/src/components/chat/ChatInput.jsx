"use client";

import { useState, useRef, useEffect } from "react";
import { Send, DescriptionOutlined } from "@mui/icons-material";
import IconButton from "@mui/material/IconButton";
import { parse } from "papaparse";
import { Table, Input, Button, Popover, message } from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  TableOutlined,
} from "@ant-design/icons";

// Styles
import styles from "./ChatInput.module.css";

export default function ChatInput({ onSendMessage }) {
  // Component States
  const [message, setMessage] = useState("");
  const [showTable, setShowTable] = useState(false);
  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [editingHeader, setEditingHeader] = useState(null);
  const [newColumnName, setNewColumnName] = useState("");

  const fileInputRef = useRef(null);
  const textAreaRef = useRef(null);

  const adjustTextAreaHeight = () => {
    const textarea = textAreaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextAreaHeight();
  }, [message]);

  const createEmptyRow = (columnList) => {
    const row = { key: Date.now().toString() };
    columnList.forEach((col) => (row[col] = ""));
    return row;
  };

  const handleCreateNewTable = () => {
    const initialColumns = ["Biomarker 1", "Biomarker 2"];
    setColumns(initialColumns);
    setData([createEmptyRow(initialColumns)]);
    setShowTable(true);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5000000) {
        message.error("File size should be less than 5MB");
        return;
      }

      parse(file, {
        complete: (results) => {
          if (results.data && results.data.length > 0) {
            const fileColumns = Object.keys(results.data[0]);
            setColumns(fileColumns);
            setData(
              results.data.map((row, index) => ({
                ...row,
                key: index.toString(),
              }))
            );
            setShowTable(true);
          }
        },
        header: true,
        skipEmptyLines: true,
      });
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeTable = () => {
    setShowTable(false);
    setColumns([]);
    setData([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const transformTableDataToCSVFormat = (columns, tableData) => {
    return tableData.map((row) => {
      // Create a new object without the 'key' property
      const csvRow = {};
      columns.forEach((column) => {
        csvRow[column] = row[column] || ""; // Ensure empty cells are represented as empty strings
      });
      return csvRow;
    });
  };

  const handleSubmit = () => {
    if (message.trim() || (showTable && data.length > 0)) {
      console.log("data2", transformTableDataToCSVFormat(columns, data));
      const newMessage = {
        content: message.trim(),
        file: showTable ? transformTableDataToCSVFormat(columns, data) : null,
      };
      onSendMessage(newMessage);
      setMessage("");
      if (textAreaRef.current) {
        textAreaRef.current.style.height = "auto";
      }
    }
  };

  const handleCellChange = (key, column, value) => {
    const newData = [...data];
    const index = newData.findIndex((item) => item.key === key);
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

    const newColumns = columns.map((col) => (col === oldName ? newName : col));
    setColumns(newColumns);

    const newData = data.map((row) => {
      const updatedRow = { ...row };
      updatedRow[newName] = row[oldName];
      delete updatedRow[oldName];
      return updatedRow;
    });
    setData(newData);
    setEditingHeader(null);
  };

  const handleDeleteColumn = (columnToDelete) => {
    try {
      if (columns.length <= 1) {
        message.error("Cannot delete the last column");
        return;
      }

      const newColumns = columns.filter((col) => col !== columnToDelete);
      const newData = data.map((row) => {
        const updatedRow = { ...row };
        delete updatedRow[columnToDelete];
        return updatedRow;
      });

      setColumns(newColumns);
      setData(newData);
      message.success(`Column "${columnToDelete}" deleted`);
    } catch (error) {
      console.error("Error deleting column:", error);
      message.error("Failed to delete column");
    }
  };

  const tableColumns = columns.map((column) => ({
    title: (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
        }}
      >
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
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <EditOutlined
            onClick={(e) => {
              e.stopPropagation();
              setEditingHeader(column);
            }}
            style={{ cursor: "pointer", fontSize: "14px" }}
          />
          <DeleteOutlined
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteColumn(column);
            }}
            style={{ cursor: "pointer", fontSize: "14px", color: "#ff4d4f" }}
          />
        </div>
      </div>
    ),
    dataIndex: column,
    key: column,
    render: (text, record) => (
      <Input
        value={text}
        onChange={(e) => handleCellChange(record.key, column, e.target.value)}
        onClick={(e) => e.stopPropagation()}
      />
    ),
  }));

  const addColumnContent = (
    <div style={{ padding: "8px", width: 250 }}>
      <Input
        placeholder="Enter biomarker name"
        value={newColumnName}
        onChange={(e) => setNewColumnName(e.target.value)}
        style={{ marginBottom: "8px" }}
      />
      <Button
        type="primary"
        onClick={() => {
          const columnName =
            newColumnName.trim() || `Column ${columns.length + 1}`;
          setColumns((prev) => [...prev, columnName]);
          setData((prev) =>
            prev.map((row) => ({
              ...row,
              [columnName]: "",
            }))
          );
          setNewColumnName("");
        }}
        block
      >
        Add Biomarker
      </Button>
    </div>
  );

  return (
    <div className={styles.chatInputContainer}>
      <div style={{ padding: "24px" }}>
        {showTable && (
          <div style={{ marginBottom: "16px" }}>
            <div
              style={{
                marginBottom: "16px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "8px"
              }}
            >
              <Popover
                content={addColumnContent}
                title="Add New Biomarker"
                trigger="click"
              >
                <Button icon={<PlusOutlined />}>Add Biomarker</Button>
              </Popover>

              <Button danger onClick={removeTable}>
                Remove Table
              </Button>
            </div>

            <Table
              dataSource={data}
              columns={tableColumns}
              pagination={false}
              bordered
              scroll={{ x: true }}
            />
          </div>
        )}
      </div>

      <div className={styles.textareaWrapper}>
        <textarea
          ref={textAreaRef}
          className={styles.chatInput}
          placeholder="How can Bloodwise help you today?"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          rows={1}
        />
        <button
          className={`${styles.submitButton} ${
            message.trim() ? styles.active : ""
          }`}
          onClick={handleSubmit}
          disabled={!message.trim() && (!showTable || data.length === 0)}
        >
          <Send />
        </button>
      </div>

      <div className={styles.inputControls}>
        <div className={`${styles.leftControls} ${styles.responsiveControls}`}>
          <input
            type="file"
            ref={fileInputRef}
            className={styles.hiddenFileInput}
            accept=".csv"
            onChange={handleFileUpload}
          />
          <div className={styles.buttonGroup}>
            <Button
              icon={<UploadOutlined />}
              onClick={() => fileInputRef.current?.click()}
              className={styles.controlButton}
            >
              Upload CSV
            </Button>
            <Button 
              icon={<TableOutlined />} 
              onClick={handleCreateNewTable}
              className={styles.controlButton}
            >
              Create New Table
            </Button>
          </div>
        </div>
        <div className={styles.rightControls}>
          <span className="text-gray-400 text-sm hidden sm:inline">
            Use shift + return for new line
          </span>
        </div>
      </div>
    </div>
  );
}
