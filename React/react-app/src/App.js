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
  // delete the UI form for the Tasks
  const deleteTask = (id) => {
    setTasks(tasks.filter((task) => task.id !== id))
  }
  // Toggle the Reminder
  const toggleReminder = (id) => {
    setTasks(tasks.map((task) => task.id === id ? {...task, reminder: !task.reminder} : task))
  }
  return (
      <div className="App">
        <Header />
        {tasks.length > 0 ? <Tasks tasks={tasks} onDelete = {deleteTask} onToggle = {toggleReminder}/> : "There is no Task"}
      </div>
    );
}
  
// class App extends React.Component{
//   render(){
//     return <h1>This is class model</h1>
//   }
// }
export default App;
