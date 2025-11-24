import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios'

function ViewMaterial ({ material }) {
    const [signedUrl, setSignedUrl] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        const ac = new AbortController();
        let active = true;

        axios.get(`https://flippedclassroom.ngrok-free.app/db/material/${material.file_id}/signed-url`, {
            signal: ac.signal
        })
        .then(response => {
            if (active) setSignedUrl(response.data.url);
        })
        .catch(e => {
            if (active) setErr("Unable to load PPTX");
        });
        return () => {
            active = false;
            ac.abort();
        }
    }, [material]);

    if (err) return (
        <div>
            {err}
        </div>
    )

    if (!signedUrl) return (
        <div>
            Loading...
        </div>
    )

    const src = "http://" + encodeURIComponent(signedUrl);

    return (
        <div className="slide-viewer">
            <iframe
            title="pptx"
            src={src}
            width="100%"
            height="720"
            frameBorder="0"
            allowFullScreen
            />
        </div>
    );
}

export default ViewMaterial;