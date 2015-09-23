/*select content_id, "sessionId"
FROM "evidenceCollector_log"
where "sessionId" in (
SELECT "sessionId"
  FROM "evidenceCollector_log"
  WHERE event = 'buy' and content_id = '20'
  order by "sessionId" )
order by content_id;
*/

--select count("sessionId") from "evidenceCollector_log" where event = 'buy'

select itemsets.*
FROM (	
	SELECT
		content_id, 
		count("sessionId") as freq,
		count("sessionId")::float / (select count("sessionId") from "evidenceCollector_log" where event = 'buy') as support
	FROM 	"evidenceCollector_log" 
	WHERE 	event = 'buy'
	GROUP BY content_id
	order by freq desc) itemsets
WHERE itemsets.support > 0.01;



(SELECT evidence.content_id, evidence."sessionId", session_count
FROM 	"evidenceCollector_log" evidence
	inner join 
	(SELECT "sessionId", count("content_id") as session_count
	FROM 	"evidenceCollector_log" 
	WHERE 	event = 'buy' 
	GROUP BY "sessionId") as sessions on evidence."sessionId" = sessions."sessionId"
WHERE   sessions.session_count > 1 and event = 'buy');


select e1.content_id, e1."sessionId", e2.content_id 
from "evidenceCollector_log" e1
inner join 
	(SELECT evidence.content_id, evidence."sessionId", session_count
	 FROM 	"evidenceCollector_log" evidence
	 inner join 
	 (
		SELECT "sessionId", count("content_id") as session_count
		FROM 	"evidenceCollector_log" 
		WHERE 	event = 'buy' 
		GROUP BY "sessionId") as sessions 
	on evidence."sessionId" = sessions."sessionId"
WHERE   sessions.session_count > 1 and event = 'buy') as e2 
on e1."sessionId" = e2."sessionId"
where e1.event = 'buy' and e1.content_id != e2.content_id
order by "sessionId";





select e1.content_id as source, e2.content_id as target, count(e2."sessionId") as freq
from "evidenceCollector_log" e1
inner join 
	(SELECT evidence.content_id, evidence."sessionId", session_count
	 FROM 	"evidenceCollector_log" evidence
	 inner join 
	 (
		SELECT "sessionId", count("content_id") as session_count
		FROM 	"evidenceCollector_log" 
		WHERE 	event = 'buy' 
		GROUP BY "sessionId") as sessions 
	on evidence."sessionId" = sessions."sessionId"
WHERE   sessions.session_count > 1 and event = 'buy') as e2 
on e1."sessionId" = e2."sessionId"
where e1.event = 'buy' 
      and e1.content_id != e2.content_id
GROUP BY e1.content_id, e2.content_id
order by freq desc, source;

