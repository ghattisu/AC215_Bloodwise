import { useState, useEffect } from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Paper from "@mui/material/Paper";

const CSVMessageTable = ({ msg, model, DataService }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  console.log("msg:", msg);
  useEffect(() => {
    const loadData = async () => {
      try {
        // If msg.file_path is present, fetch the data
        if (msg.file_path) {
          try {
            const fileData = await DataService.GetChatMessageFile(
              model,
              msg.file_path
            );
            console.log("fileData test:", fileData);
            if (fileData) {
              setData(fileData["data"]);
              console.log("Data loaded:", fileData["data"]);
            }
          } catch (serviceError) {
            console.warn(
              "DataService failed, falling back to direct fetch:",
              serviceError
            );
          }
        }

        setLoading(false);
      } catch (err) {
        console.error("Error loading data:", err);
        setError(err.message);
        setLoading(false);
      }
    };

    loadData();
  }, [msg, model]);

  if (loading) {
    return <div>Loading data...</div>;
  }

  if (error) {
    return <div>Error loading data: {error}</div>;
  }

  if (!data || data.length === 0) {
    return null;
  }

  console.log("Data:", data);

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            {Object.keys(
              data[0]
            ).map((header) => (
              <TableCell key={header}>{header}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
        <TableRow>
            {Object.values(data[0]).map((value, index) => (
              <TableCell key={index}>{value}</TableCell>
            ))}
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default CSVMessageTable;
