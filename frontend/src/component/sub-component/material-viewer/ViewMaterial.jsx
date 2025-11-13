import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios'

function ViewMaterial ({ material }, { activeSection }) {
    const [signedUrl, setSignedUrl] = useState(null);
    const [err, setErr] = useState(null);

    useEffect(() => {
        if (activeSection !== 'material-viewer') return;
        const ac = new AbortController();
        let active = true;

        axios.get(`/material/${material.file_id}/signed-url`, {
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
    }, [activeSection, material]);

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

    const src = "https://view.officeapps.live.com/op/embed.aspx?src=" + encodeURIComponent(signedUrl);

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