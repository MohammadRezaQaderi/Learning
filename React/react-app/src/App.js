import Header from "./components/Header";
import Tasks from "./components/Tasks";
import { useState } from "react"

// import React from "react";
function App() {
  const [tasks, setTasks] = useState([
    {
        id: 1,
        text: "ssss",
        day: "fev ,",
        reminder: true,
    },
    {
        id: 2,
        text: "dddd",
        day: "much ,",
        reminder: true,
    },
  ])
  const deleteTask = (id) => {
    console.log('deleted ', id);
  }
  return (
      <div className="App">
        <Header />
        <Tasks tasks={tasks} onDelete = {deleteTask}/>
      </div>
    );
}
  
// class App extends React.Component{
//   render(){
//     return <h1>This is class model</h1>
//   }
// }
export default App;
