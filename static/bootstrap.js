
applyLang();updateBudget(10000);restoreSession();
for(const id of ["idea","category","user_type","budget","region","context"]){const field=document.getElementById(id);field.addEventListener("input",saveSession);field.addEventListener("change",saveSession);}
document.getElementById("idea").addEventListener("input",()=>{selectedIdeaSource="user_input";saveSession();});
document.getElementById("discovery-results").addEventListener("click",event=>{if(event.target.closest(".idea-card button"))selectedIdeaSource="ai_suggestion_selected";},true);
document.getElementById("newBtn").addEventListener("click",()=>{selectedIdeaSource="user_input";},true);

setupV2();
