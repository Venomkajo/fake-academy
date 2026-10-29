import { UserPublic } from "../../api/auth"
import { fetchUserById } from "../../api/admin"
import { updateUser } from "../../api/admin"

import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query";

export default function EditUserPage() {

    const { id } = useParams<{ id: string }>();

    const userQuery = useQuery({
        queryKey: ['admin_user', id],
        queryFn: () => fetchUserById(Number(id)),
    })

    if (userQuery.isLoading) {
        return <p>Ładowanie...</p>
    }

    function handleSaveChanges() {
      const updated_user = {
        id: Number(id),
        first_name: (document.getElementById("first_name") as HTMLInputElement).value,
        last_name: (document.getElementById("last_name") as HTMLInputElement).value,
        email: (document.getElementById("email") as HTMLInputElement).value,
        role: (document.getElementById("role") as HTMLSelectElement).value as UserPublic["role"],
        is_active: (document.getElementById("is_active") as HTMLSelectElement).value === "true",
      }

      updateUser(Number(id), updated_user);
    }

  return (
    <section>
      <div>
        <h1>Użytkownik {userQuery.data?.first_name} {userQuery.data?.last_name}:</h1>
        <p><label htmlFor="first_name">Imię:</label> <input id="first_name" defaultValue={userQuery.data?.first_name}></input></p>
        <p><label htmlFor="last_name">Nazwisko:</label> <input id="last_name" defaultValue={userQuery.data?.last_name}></input></p>
        <p><label htmlFor="email">Email:</label> <input id="email" defaultValue={userQuery.data?.email}></input></p>
        <p><label htmlFor="role">Rola:</label> <select id="role" defaultValue={userQuery.data?.role} >
          <option value="student">Student</option>
          <option value="teacher">Nauczyciel</option>
          <option value="admin">Administrator</option>
        </select>
        </p>
        <p><label htmlFor="is_active">Aktywny:</label> <select id="is_active" defaultValue={userQuery.data?.is_active ? "true" : "false"} >
          <option value="true">Tak</option>
          <option value="false">Nie</option>
        </select>
        </p>
        <button className="btn btn-outline-primary edit-user-button" onClick={handleSaveChanges}>
          Zapisz zmiany
        </button>
      </div>
      <div>

      </div>
    </section>
  )
}