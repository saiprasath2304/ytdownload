document.addEventListener('DOMContentLoaded', () => {
    const videoForm = document.getElementById('videoForm');
    const responseMessage = document.getElementById('responseMessage');
    const downloadMessage = document.getElementById('downloadMessage');
    const videoDownload = document.getElementById('videoDownload');
    document.getElementById("clearText").onclick = function(){
        document.getElementById("video_url").value = "";
    };
    document.getElementById("reLoad").onclick = function(){
        document.getElementById("reloadIcon").classList.add("fa-spin");
        setTimeout(function() {
            window.location.reload();
        }, 2000);
    };    

    videoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        document.getElementById('videoBtn').style.display = 'none';
        document.getElementById('videoIcon').classList.remove('hidden');
        document.getElementById('videoIcon').classList.add('block');

        const videoUrl = document.getElementById('video_url').value;
        if (!(videoUrl.includes('youtube') || videoUrl.includes('youtu.be'))) {
            alert("Sairam! only youtube links are allowed!")
            window.location.reload();
        }

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    video_url: videoUrl
                })
            });

            const data = await response.json();
            if (data.success) {
                const thumbnailUrl = data.info['thumbnail'];
                const channelName = data.info['channel'];
                const videoFormats = data.info['formats'];
                // console.log(videoFormats.length)
                if (channelName.includes('Sri Sathya Sai')){
                
                    document.getElementById('videoIcon').classList.remove('block');
                    document.getElementById('videoIcon').classList.add('hidden');
                    responseMessage.innerHTML = `<span class="text-green-500">Video information retrieved successfully!</span><br>`
                    + data.info['fulltitle'] + `<br>
                    <div class="relative inline-block">
                        <img src="${thumbnailUrl}" alt="Video Thumbnail" class="mt-4 rounded shadow-lg w-1/2 inline">&nbsp;
                        <a id="thumbDown" class="absolute bottom-2 cursor-pointer" title="Download thumbnail">
                            <i class="fa-solid fa-download fa-xl "></i>
                        </a>
                    </div>`;
                    document.getElementById("thumbDown").onclick = function(e){
                        const downloadUrl = `/download-image?url=${encodeURIComponent(thumbnailUrl)}`; // Encode the URL for the query string
                    
                        window.location.href = downloadUrl;
                    };
                    downloadMessage.innerHTML = `<div class="block space-x-2">
                                                    <button id="vdown" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">Video (.mp4)</button>
                                                    <button id="adown" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">Audio (.m4a)</button>
                                                </div>`;
                    var vDown;
                    var aDown;
                    for(i=0; i<videoFormats.length; i++){
                        // videoDownload.innerHTML += '<div>'+`${videoFormats[i]['url']}` + '<br></div>';
                        // console.log(videoFormats[i]['url'])
                        const vdoFormat = videoFormats[i]['format']
                        // console.log(vdoFormat)
                        if (vdoFormat.includes('140-drc - audio only (medium, DRC)')){
                            // console.log("audio only links",videoFormats[i]['url'])
                            aDown = videoFormats[i]['url']
                        }
                        if (data.info){
                            // console.log("video only links",videoFormats[i]['url'])
                            if(videoFormats[i]['ext'] == 'mp4' && (videoFormats[i]['url'].includes('https://rr')) && videoFormats[i]['format'].includes('1920x1080')){
                                vDown = videoFormats[i]['url']
                                // console.log(videoFormats[i]['url'])
                            }
                            
                        }
                    }
                    document.getElementById("vdown").onclick = function(e){
                        // console.log(vDown)
                        // console.log("Hi")
                        window.open(vDown, '_blank');
                    };
                    document.getElementById("adown").onclick = function(e){
                        // console.log(aDown)
                        // console.log("Hi")
                        window.open(aDown, '_blank');
                    };
                    console.log(data.info);
                }else{
                    responseMessage.innerHTML = alert('Sairam! you are not allowed to download videos from channels other than Sri Sathya Sai');
                    document.getElementById('videoIcon').classList.remove('block');
                    document.getElementById('videoIcon').classList.add('hidden');
                    window.location.reload();
                }
            } else {
                responseMessage.innerHTML = `<span class="text-red-500">Error: ${data.error}</span>`;
            }
        } catch (error) {
            responseMessage.innerHTML = `<span class="text-red-500">Error: ${error.message}</span>`;
        }
    });
});
