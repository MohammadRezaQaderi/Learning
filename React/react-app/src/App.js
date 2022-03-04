import Header from "./components/Header";
import Tasks from "./components/Tasks";
import AddTask from "./components/AddTask";
import { useState } from "react"

// import React from "react";
function App() {
  const [showAddTask, setShowAddTask] = useState(false)
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

  // Add tasks
  const addTask = (task) =>{
    const id = Math.floor(Math.random()*555)+27
    //make new task
    const newTask = {id, ...task}
    // added to previous tasks
    setTasks([...tasks, newTask]) 
  }

  return (
      <div className="App">
        <Header onAdd={() => setShowAddTask(!showAddTask) } showAdd = {showAddTask} />
        {showAddTask && <AddTask onAdd={addTask} />}
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
